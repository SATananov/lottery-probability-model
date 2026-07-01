from __future__ import annotations

import csv
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v91_budget_aware_system_builder_engine import (
    DEFAULT_PRICE_PER_COMBINATION,
    DRAW_SIZE,
    TOTAL_NUMBERS,
    _combo_balance_score,
    _dedupe_combinations,
    _historical_exact_matches,
    _model_mean,
    _select_reduced_combinations,
    build_system_option,
    calculate_empty_risk,
    combination_pairs,
    combination_triples,
    load_historical_draw_sets,
    load_number_scores,
    safe_comb,
    score_system_option,
    unique_numbers,
)
from src.v109_2_ticket_pack_4line_engine import LINES_PER_TICKET, validate_numbers
from src.v109_sqlite_journal_engine import active_plan_metadata, format_numbers, initialize_database
from src.v116_1_real_ticket_pack_ui_polish import format_eur, safe_float, safe_int

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v118"

SUMMARY_JSON = REPORTS_DIR / "v118_model_system_ticket_builder_summary.json"
SUMMARY_MD = REPORTS_DIR / "v118_model_system_ticket_builder_summary.md"
SYSTEM_TABLE_CSV = REPORTS_DIR / "v118_full_system_price_table.csv"
PACK_CSV = REPORTS_DIR / "v118_model_system_ticket_pack.csv"
COPY_TEXT = REPORTS_DIR / "v118_model_system_ticket_pack_copy.txt"
CHECKLIST_CSV = REPORTS_DIR / "v118_model_system_ticket_builder_checklist.csv"
MODEL_JSON = MODELS_DIR / "model_system_ticket_builder_status.json"

STEP_NAME = "Step 118 — Model System Ticket Builder"
STATUS_READY = "MODEL_SYSTEM_TICKET_BUILDER_READY"
STATUS_CHECK_REQUIRED = "CHECK_REQUIRED"

DEFAULT_CORE_SIZE = 9
DEFAULT_TARGET_LINES = 12
DEFAULT_SOURCE = "hybrid"
SOURCE_LABELS_BG = {
    "model": "Само моделни числа",
    "pack": "Числа от готовия пакет",
    "hybrid": "Хибрид: готов пакет + моделни оценки",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _normalize_number(value: Any) -> int | None:
    try:
        number = int(float(str(value).strip()))
    except Exception:
        return None
    return number if 1 <= number <= TOTAL_NUMBERS else None


def _numbers_key(numbers: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(number) for number in numbers))


def _sorted_by_model_score(numbers: list[int], number_scores: dict[int, float]) -> list[int]:
    unique = sorted({int(number) for number in numbers if 1 <= int(number) <= TOTAL_NUMBERS})
    return sorted(unique, key=lambda number: (-float(number_scores.get(number, 0.0)), number))


def load_model_number_ranking(limit: int = 18) -> list[dict[str, Any]]:
    scores = load_number_scores()
    ranking = sorted(range(1, TOTAL_NUMBERS + 1), key=lambda number: (-float(scores.get(number, 0.0)), number))
    return [
        {
            "rank": index,
            "number": number,
            "model_score": round(float(scores.get(number, 0.0)), 3),
        }
        for index, number in enumerate(ranking[: max(1, int(limit or 18))], start=1)
    ]


def load_current_pack_numbers() -> list[int]:
    payload = _load_json(REPORTS_DIR / "v117_real_ticket_pack_builder_summary.json")
    numbers: list[int] = []
    if isinstance(payload, dict):
        for card in payload.get("cards", []) or []:
            if not isinstance(card, dict):
                continue
            for line in card.get("lines", []) or []:
                if not isinstance(line, dict):
                    continue
                for raw in line.get("numbers", []) or []:
                    number = _normalize_number(raw)
                    if number is not None:
                        numbers.append(number)
    return sorted(set(numbers))


def build_model_core(source: str, core_size: int, number_scores: dict[int, float] | None = None) -> list[int]:
    scores = number_scores or load_number_scores()
    size = max(DRAW_SIZE + 1, min(12, int(core_size or DEFAULT_CORE_SIZE)))
    model_numbers = [row["number"] for row in load_model_number_ranking(49)]
    pack_numbers = _sorted_by_model_score(load_current_pack_numbers(), scores)

    pool: list[int] = []
    source_key = str(source or DEFAULT_SOURCE).strip().lower()
    if source_key == "model":
        candidates = model_numbers
    elif source_key == "pack":
        candidates = pack_numbers + model_numbers
    else:
        # Keep the current real pack connected to the app, then fill with the strongest model-ranked balls.
        candidates = pack_numbers[: max(DRAW_SIZE, size - 2)] + model_numbers

    for number in candidates:
        if number not in pool:
            pool.append(int(number))
        if len(pool) >= size:
            break
    return sorted(pool)


def build_full_system_price_table(price_per_line: float = DEFAULT_PRICE_PER_COMBINATION) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for size in range(7, 13):
        combinations = safe_comb(size, DRAW_SIZE)
        rows.append({
            "system_numbers": size,
            "combinations": combinations,
            "tickets_4_lines": math.ceil(combinations / LINES_PER_TICKET),
            "price_per_line_eur": round(float(price_per_line), 2),
            "total_price_eur": round(combinations * float(price_per_line), 2),
            "total_price_label": format_eur(combinations * float(price_per_line)),
        })
    return rows


def _system_label(core_source: str, core_size: int, full_system: bool, selected_count: int) -> str:
    source_label = SOURCE_LABELS_BG.get(str(core_source or DEFAULT_SOURCE), SOURCE_LABELS_BG["hybrid"])
    if full_system:
        return f"Пълна система от {core_size} числа · {source_label}"
    return f"Редуцирана система от {core_size} числа · {selected_count} комбинации · {source_label}"


def _build_option(
    *,
    core_source: str,
    core_size: int,
    target_lines: int,
    full_system: bool,
    price_per_line: float,
) -> dict[str, Any]:
    scores = load_number_scores()
    historical_sets = load_historical_draw_sets()
    pool = build_model_core(core_source, core_size, scores)
    possible = safe_comb(len(pool), DRAW_SIZE)
    selected_count = possible if full_system else max(1, min(int(target_lines or DEFAULT_TARGET_LINES), possible))
    mode = "full" if full_system else "reduced"
    option = build_system_option(
        option_id="step118_model_system",
        label=_system_label(core_source, len(pool), full_system, selected_count),
        source="model" if core_source == "model" else "hybrid",
        pool=pool,
        mode=mode,
        target_count=selected_count,
        price_per_combination=float(price_per_line),
        number_scores=scores,
        historical_sets=historical_sets,
    )
    option["core_source"] = core_source
    option["core_source_label_bg"] = SOURCE_LABELS_BG.get(core_source, SOURCE_LABELS_BG["hybrid"])
    option["price_per_line_eur"] = round(float(price_per_line), 2)
    option["selected_for_real_pack"] = not full_system and selected_count == DEFAULT_TARGET_LINES
    return option


def _line_role(index: int, full_system: bool) -> str:
    if full_system:
        return "пълна системна комбинация"
    roles = [
        "ядро + моделна сила",
        "различно покритие",
        "баланс ниски/средни/високи",
        "покритие на двойки",
    ]
    return roles[(index - 1) % len(roles)]


def build_cards_from_option(option: dict[str, Any]) -> list[dict[str, Any]]:
    combinations = option.get("combinations", []) or []
    full_system = option.get("mode") == "full"
    cards: list[dict[str, Any]] = []
    for card_index, start in enumerate(range(0, len(combinations), LINES_PER_TICKET), start=1):
        chunk = combinations[start:start + LINES_PER_TICKET]
        lines: list[dict[str, Any]] = []
        for offset, combo in enumerate(chunk, start=1):
            global_index = start + offset
            nums = sorted(int(number) for number in combo)
            lines.append({
                "line_no": offset,
                "global_line_no": global_index,
                "role": _line_role(global_index, full_system),
                "numbers": nums,
                "numbers_text": format_numbers(nums),
                "system_core": option.get("core_numbers", []),
                "model_strength_score": option.get("model_strength_score", 0.0),
            })
        cards.append({
            "ticket_no": card_index,
            "title": f"Системен фиш {card_index}",
            "subtitle": f"{len(chunk)} комбинации от {option.get('label', 'системен пакет')}",
            "strategy": "системен модел",
            "source_note": "Числата са взети от моделния ранг и текущия готов пакет, не са ръчно измислени.",
            "line_count": len(lines),
            "lines": lines,
        })
    return cards


def _copy_text(option: dict[str, Any], cards: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "СИСТЕМЕН ФИШ ОТ МОДЕЛИТЕ — 6/49",
        f"Ядро: {format_numbers(option.get('core_numbers', []))}",
        f"Режим: {option.get('mode_label', '')}",
        f"Комбинации: {option.get('selected_combinations', 0)}",
        f"Цена: {format_eur(option.get('cost_eur', 0.0))}",
        "Важно: статистическа подредба, не гаранция за печалба.",
        "",
    ]
    for card in cards:
        lines.append(str(card.get("title") or "Фиш"))
        for line in card.get("lines", []) or []:
            lines.append(f"Ред {line.get('line_no')}: {line.get('numbers_text')}")
        lines.append("")
    return "\n".join(lines).strip()


def _flatten_cards(cards: list[dict[str, Any]], price_per_line: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for card in cards:
        for line in card.get("lines", []) or []:
            rows.append({
                "ticket_no": card.get("ticket_no"),
                "line_no": line.get("line_no"),
                "global_line_no": line.get("global_line_no"),
                "numbers_text": line.get("numbers_text"),
                "role_bg": line.get("role"),
                "price_eur": round(float(price_per_line), 2),
            })
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_model_system_ticket_builder(
    *,
    core_source: str = DEFAULT_SOURCE,
    core_size: int = DEFAULT_CORE_SIZE,
    target_lines: int = DEFAULT_TARGET_LINES,
    full_system: bool = False,
    price_per_line: float | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()

    metadata = active_plan_metadata()
    price = safe_float(price_per_line, 0.0)
    if price <= 0:
        price = safe_float(metadata.get("price_per_line_eur"), DEFAULT_PRICE_PER_COMBINATION) or DEFAULT_PRICE_PER_COMBINATION

    core_source_key = str(core_source or DEFAULT_SOURCE).strip().lower()
    if core_source_key not in SOURCE_LABELS_BG:
        core_source_key = DEFAULT_SOURCE

    option = _build_option(
        core_source=core_source_key,
        core_size=safe_int(core_size, DEFAULT_CORE_SIZE),
        target_lines=safe_int(target_lines, DEFAULT_TARGET_LINES),
        full_system=bool(full_system),
        price_per_line=price,
    )
    cards = build_cards_from_option(option)
    copy_text = _copy_text(option, cards)
    full_table = build_full_system_price_table(price)
    ranking = load_model_number_ranking(18)
    pack_numbers = load_current_pack_numbers()

    checks: list[dict[str, Any]] = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checks.append({
            "check": name,
            "status": "OK" if passed else "FAIL",
            "blocking": blocking,
            "details_bg": details_bg,
        })

    combos = option.get("combinations", []) or []
    combo_keys = [_numbers_key([int(n) for n in combo]) for combo in combos]
    all_valid = True
    for combo in combos:
        valid, _message = validate_numbers([int(n) for n in combo])
        all_valid = all_valid and valid

    add_check("model_numbers_available", len(ranking) >= 12, f"моделно класирани числа={len(ranking)}")
    add_check("core_has_requested_size", len(option.get("core_numbers", [])) == safe_int(core_size, DEFAULT_CORE_SIZE), f"ядро={format_numbers(option.get('core_numbers', []))}")
    add_check("combinations_created", len(combos) > 0, f"комбинации={len(combos)}")
    add_check("all_combinations_valid", all_valid, "всяка комбинация има 6 уникални числа между 1 и 49")
    add_check("no_duplicate_combinations", len(combo_keys) == len(set(combo_keys)), f"редове={len(combo_keys)}, уникални={len(set(combo_keys))}")
    add_check("default_real_pack_shape", (not full_system and len(combos) == DEFAULT_TARGET_LINES and all(len(card.get('lines', [])) == LINES_PER_TICKET for card in cards)) or bool(full_system), "редуцираният пакет е 3 фиша × 4 комбинации", blocking="no")
    add_check("current_pack_link_available", len(pack_numbers) > 0, f"числа от готовия пакет={len(pack_numbers)}", blocking="no")

    blocking_failures = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    status = STATUS_READY if blocking_failures == 0 else STATUS_CHECK_REQUIRED

    summary = {
        "step": "118",
        "name": STEP_NAME,
        "status": status,
        "blocking_failures": blocking_failures,
        "core_source": core_source_key,
        "core_source_label_bg": SOURCE_LABELS_BG[core_source_key],
        "core_size": len(option.get("core_numbers", [])),
        "core_numbers": option.get("core_numbers", []),
        "mode": option.get("mode"),
        "mode_label": option.get("mode_label"),
        "selected_combinations": option.get("selected_combinations", 0),
        "possible_full_combinations": option.get("possible_full_combinations", 0),
        "price_per_line_eur": round(float(price), 2),
        "total_price_eur": option.get("cost_eur", 0.0),
        "total_price_label": format_eur(option.get("cost_eur", 0.0)),
        "ticket_count": len(cards),
        "lines_per_ticket": LINES_PER_TICKET,
        "system_score": option.get("system_score", 0.0),
        "model_strength_score": option.get("model_strength_score", 0.0),
        "balance_score": option.get("balance_score", 0.0),
        "pair_coverage_percent": option.get("pair_coverage_percent", 0.0),
        "triple_coverage_percent": option.get("triple_coverage_percent", 0.0),
        "pool_coverage_percent": option.get("pool_coverage_percent", 0.0),
        "empty_risk_percent": option.get("empty_risk_percent", 0.0),
        "at_least_one_hit_percent": option.get("at_least_one_hit_percent", 0.0),
        "historical_exact_matches": option.get("historical_exact_matches", 0),
        "model_number_ranking": ranking,
        "current_pack_numbers": pack_numbers,
        "full_system_price_table": full_table,
        "cards": cards,
        "checks": checks,
        "safe_note_bg": "Системният фиш използва числа от моделните оценки и текущия готов пакет. Това е метод за организация на фишове, не гаранция за печалба.",
        "generated_at_utc": utc_now(),
        "copy_text_path": str(COPY_TEXT.relative_to(ROOT)),
        "csv_path": str(PACK_CSV.relative_to(ROOT)),
    }

    if write_outputs:
        SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        MODEL_JSON.write_text(json.dumps({
            "step": summary["step"],
            "status": summary["status"],
            "blocking_failures": summary["blocking_failures"],
            "core_numbers": summary["core_numbers"],
            "selected_combinations": summary["selected_combinations"],
            "total_price_eur": summary["total_price_eur"],
            "generated_at_utc": summary["generated_at_utc"],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        COPY_TEXT.write_text(copy_text + "\n", encoding="utf-8")
        _write_csv(SYSTEM_TABLE_CSV, full_table, ["system_numbers", "combinations", "tickets_4_lines", "price_per_line_eur", "total_price_eur", "total_price_label"])
        _write_csv(PACK_CSV, _flatten_cards(cards, price), ["ticket_no", "line_no", "global_line_no", "numbers_text", "role_bg", "price_eur"])
        _write_csv(CHECKLIST_CSV, checks, ["check", "status", "blocking", "details_bg"])

        md_lines = [
            "# Step 118 — Model System Ticket Builder",
            "",
            f"- Status: `{status}`",
            f"- Blocking failures: `{blocking_failures}`",
            f"- Източник: **{summary['core_source_label_bg']}**",
            f"- Ядро: **{format_numbers(summary['core_numbers'])}**",
            f"- Режим: **{summary['mode_label']}**",
            f"- Комбинации: **{summary['selected_combinations']}**",
            f"- Цена: **{summary['total_price_label']}**",
            f"- Оценка: **{summary['system_score']}**",
            "",
            "## Пълни системи при текущата цена",
            "",
        ]
        for row in full_table:
            md_lines.append(f"- {row['system_numbers']} числа: `{row['combinations']}` комбинации · `{row['total_price_label']}`")
        md_lines.extend(["", "## Готов системен пакет", ""])
        for card in cards:
            md_lines.append(f"### {card.get('title')}")
            for line in card.get("lines", []) or []:
                md_lines.append(f"- Ред {line.get('line_no')}: `{line.get('numbers_text')}`")
            md_lines.append("")
        md_lines.extend(["## Проверки", ""])
        for check in checks:
            md_lines.append(f"- `{check['status']}` — {check['check']}: {check['details_bg']}")
        SUMMARY_MD.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")

    return summary


def load_summary() -> dict[str, Any]:
    if not SUMMARY_JSON.exists():
        return {}
    try:
        return json.loads(SUMMARY_JSON.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def print_summary(summary: dict[str, Any]) -> None:
    print(f"STEP_118_STATUS {summary.get('status')}")
    print(f"BLOCKING_FAILURES {summary.get('blocking_failures')}")
    print(f"CORE {' '.join(str(n) for n in summary.get('core_numbers', []))}")
    print(f"COMBINATIONS {summary.get('selected_combinations')}")
    print(f"TOTAL_PRICE_EUR {summary.get('total_price_eur')}")
    print(f"BAD_COUNT {summary.get('blocking_failures')}")
