from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.v109_2_ticket_pack_4line_engine import (
    DEFAULT_TICKET_COUNT,
    LINES_PER_TICKET,
    build_suggested_ticket_cards,
    normalize_cards_from_ui,
    validate_numbers,
)
from src.v109_sqlite_journal_engine import active_plan_metadata, default_next_sunday, initialize_database, latest_draw_from_dataset
from src.v116_1_real_ticket_pack_ui_polish import build_copy_text, format_eur, safe_float, safe_int

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v117"

SUMMARY_JSON = REPORTS_DIR / "v117_real_ticket_pack_builder_summary.json"
SUMMARY_MD = REPORTS_DIR / "v117_real_ticket_pack_builder_summary.md"
PACK_CSV = REPORTS_DIR / "v117_real_ticket_pack_builder_cards.csv"
COPY_TEXT = REPORTS_DIR / "v117_real_ticket_pack_builder_copy.txt"
CHECKLIST_CSV = REPORTS_DIR / "v117_real_ticket_pack_builder_checklist.csv"
MODEL_JSON = MODELS_DIR / "real_ticket_pack_builder_status.json"

STEP_NAME = "Step 117 — Real Ticket Pack Builder"
STATUS_READY = "REAL_TICKET_PACK_BUILDER_READY"
STATUS_CHECK_REQUIRED = "CHECK_REQUIRED"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _numbers_key(numbers: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(number) for number in numbers))


def _card_copy_text(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return "Няма готов фиш пакет."
    lines: list[str] = [
        "ГОТОВ ФИШ ПАКЕТ — 6/49",
        "Важно: това е статистически подреден пакет, не гаранция за печалба.",
        "",
    ]
    for card in cards:
        title = str(card.get("title") or card.get("display_name") or f"Фиш {card.get('ticket_no', '')}").strip()
        lines.append(title)
        lines.append(f"Стратегия: {card.get('strategy') or '—'}")
        for line in card.get("lines", []):
            lines.append(f"Ред {line.get('line_no')}: {line.get('numbers_text')}")
        lines.append("")
    return "\n".join(lines).strip()


def _flatten_cards(cards: list[dict[str, Any]], price_per_line: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for card_index, card in enumerate(cards, start=1):
        card_title = str(card.get("title") or f"Фиш {card_index}")
        for line in card.get("lines", []):
            numbers = [safe_int(number) for number in line.get("numbers", [])]
            rows.append({
                "ticket_no": card_index,
                "ticket_title_bg": card_title,
                "line_no": safe_int(line.get("line_no"), len(rows) + 1),
                "numbers_text": line.get("numbers_text") or ", ".join(str(n) for n in numbers),
                "role_bg": line.get("role") or card.get("strategy") or "комбинация",
                "strategy_bg": card.get("strategy") or "—",
                "source_note_bg": card.get("source_note") or "—",
                "price_eur": round(price_per_line, 2),
            })
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _latest_draw_date_from_summary(summary: dict[str, Any]) -> str:
    latest = summary.get("latest_dataset_draw")
    if isinstance(latest, dict) and str(latest.get("date") or "").strip():
        return str(latest.get("date")).strip()
    for card in summary.get("cards", []) or []:
        if not isinstance(card, dict):
            continue
        context = card.get("source_context")
        if isinstance(context, dict) and str(context.get("latest_draw_date") or "").strip():
            return str(context.get("latest_draw_date")).strip()
    return ""


def _current_latest_draw_date() -> str:
    latest = latest_draw_from_dataset()
    return str(latest.get("date") or "").strip()


def is_summary_current(summary: dict[str, Any]) -> bool:
    if not summary:
        return False
    summary_latest = _latest_draw_date_from_summary(summary)
    current_latest = _current_latest_draw_date()
    return bool(summary_latest and current_latest and summary_latest == current_latest)


def ensure_current_real_ticket_pack_summary(
    ticket_count: int = DEFAULT_TICKET_COUNT,
    package_mode: str = "extended",
) -> dict[str, Any]:
    summary = load_summary()
    if is_summary_current(summary):
        return summary
    return build_real_ticket_pack_builder(ticket_count=ticket_count, package_mode=package_mode)


def _next_target_draw_date_label() -> str:
    try:
        return default_next_sunday(date.today()).isoformat()
    except Exception:
        return ""


def build_real_ticket_pack_builder(ticket_count: int = DEFAULT_TICKET_COUNT, package_mode: str = "extended") -> dict[str, Any]:
    """Build a practical physical-ticket pack: 1 ticket = 4 combinations.

    This step does not change the probability model. It turns the selected recommendations
    into a user-facing pack for copying, printing and optionally saving as played.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()

    cards = build_suggested_ticket_cards(ticket_count=int(ticket_count or DEFAULT_TICKET_COUNT), package_mode=package_mode)
    normalized_cards, issues = normalize_cards_from_ui(cards)
    metadata = active_plan_metadata()
    latest_draw = latest_draw_from_dataset()
    price_per_line = safe_float(metadata.get("price_per_line_eur"), 0.9) or 0.9
    rows = _flatten_cards(normalized_cards, price_per_line)
    copy_text = _card_copy_text(normalized_cards)

    all_keys: list[tuple[int, ...]] = []
    all_valid = True
    for card in normalized_cards:
        for line in card.get("lines", []):
            numbers = [safe_int(number) for number in line.get("numbers", [])]
            valid, _ = validate_numbers(numbers)
            all_valid = all_valid and valid
            if valid:
                all_keys.append(_numbers_key(numbers))

    checks: list[dict[str, Any]] = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checks.append({
            "check": name,
            "status": "OK" if passed else "FAIL",
            "blocking": blocking,
            "details_bg": details_bg,
        })

    requested_count = int(ticket_count or DEFAULT_TICKET_COUNT)
    add_check("cards_created", len(normalized_cards) > 0, f"фишове={len(normalized_cards)}")
    add_check("requested_ticket_count", len(normalized_cards) == requested_count, f"поискани={requested_count}, подготвени={len(normalized_cards)}")
    add_check("each_ticket_has_four_lines", all(len(card.get("lines", [])) == LINES_PER_TICKET for card in normalized_cards), json.dumps([len(card.get("lines", [])) for card in normalized_cards], ensure_ascii=False))
    add_check("all_lines_have_valid_numbers", all_valid and not issues, "всяка комбинация има 6 уникални числа между 1 и 49")
    add_check("no_duplicate_combinations_inside_pack", len(all_keys) == len(set(all_keys)), f"редове={len(all_keys)}, уникални={len(set(all_keys))}")
    add_check("copy_text_available", bool(copy_text.strip()), f"символи={len(copy_text)}", blocking="no")

    blocking_failures = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    status = STATUS_READY if blocking_failures == 0 else STATUS_CHECK_REQUIRED
    total_lines = sum(len(card.get("lines", [])) for card in normalized_cards)
    total_price = round(price_per_line * total_lines, 2)

    summary = {
        "step": "117",
        "name": STEP_NAME,
        "status": status,
        "blocking_failures": blocking_failures,
        "ticket_count": len(normalized_cards),
        "lines_per_ticket": LINES_PER_TICKET,
        "total_lines": total_lines,
        "price_per_line_eur": round(price_per_line, 2),
        "total_price_eur": total_price,
        "total_price_label": format_eur(total_price),
        "package_mode": package_mode,
        "plan_id": metadata.get("plan_id") or "",
        "strategy_type": metadata.get("strategy_type") or "",
        "latest_dataset_draw": latest_draw,
        "latest_dataset_draw_date": latest_draw.get("date") or "",
        "next_target_draw_date": _next_target_draw_date_label(),
        "cards": normalized_cards,
        "copy_text_path": str(COPY_TEXT.relative_to(ROOT)),
        "csv_path": str(PACK_CSV.relative_to(ROOT)),
        "safe_note_bg": "Step 117 подрежда реален пакет за пускане. Той не обещава печалба и не променя вероятностите.",
        "generated_at_utc": utc_now(),
        "checks": checks,
        "issues": issues,
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": summary["step"],
        "status": summary["status"],
        "blocking_failures": summary["blocking_failures"],
        "ticket_count": summary["ticket_count"],
        "lines_per_ticket": summary["lines_per_ticket"],
        "total_lines": summary["total_lines"],
        "total_price_eur": summary["total_price_eur"],
        "generated_at_utc": summary["generated_at_utc"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    COPY_TEXT.write_text(copy_text + "\n", encoding="utf-8")
    _write_csv(PACK_CSV, rows, [
        "ticket_no",
        "ticket_title_bg",
        "line_no",
        "numbers_text",
        "role_bg",
        "strategy_bg",
        "source_note_bg",
        "price_eur",
    ])
    _write_csv(CHECKLIST_CSV, checks, ["check", "status", "blocking", "details_bg"])

    md_lines = [
        "# Step 117 — Real Ticket Pack Builder",
        "",
        f"- Status: `{status}`",
        f"- Blocking failures: `{blocking_failures}`",
        f"- Фишове: `{summary['ticket_count']}`",
        f"- Комбинации във фиш: `{LINES_PER_TICKET}`",
        f"- Общо комбинации: `{total_lines}`",
        f"- Обща цена: `{summary['total_price_label']}`",
        "",
        "## Готов пакет",
        "",
    ]
    for card in normalized_cards:
        md_lines.append(f"### {card.get('title') or 'Фиш'}")
        for line in card.get("lines", []):
            md_lines.append(f"- Ред {line.get('line_no')}: `{line.get('numbers_text')}`")
        md_lines.append("")
    md_lines.extend([
        "## Проверки",
        "",
    ])
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
    print(f"STEP_117_STATUS {summary.get('status')}")
    print(f"BLOCKING_FAILURES {summary.get('blocking_failures')}")
    print(f"TICKETS {summary.get('ticket_count')}")
    print(f"LINES {summary.get('total_lines')}")
    print(f"TOTAL_PRICE_EUR {summary.get('total_price_eur')}")
    print(f"BAD_COUNT {summary.get('blocking_failures')}")
