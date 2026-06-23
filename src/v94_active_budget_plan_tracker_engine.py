from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v93_budget_advisor_engine import (
    DEFAULT_PRICE_PER_COMBINATION,
    PREFERENCE_LABELS,
    build_budget_advice,
)

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v94" / "v94_active_budget_plan_tracker_model.json"
ACTIVE_PLAN_PATH = ROOT / "reports" / "v94_active_budget_plan.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v94_active_budget_plan_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v94_active_budget_plan_summary.md"
HISTORY_CSV_PATH = ROOT / "reports" / "v94_active_budget_plan_history.csv"
LATEST_RESULT_CSV_PATH = ROOT / "reports" / "v94_latest_plan_result.csv"
CANONICAL_DRAWS_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"

DRAW_SIZE = 6
MIN_NUMBER = 1
MAX_NUMBER = 49

SAFE_NOTE_BG = (
    "Това е дневник за план и резултат. Запазва препоръка преди следващ тираж и после я сравнява "
    "с новия реален тираж. Не е прогноза, не е гаранция и не доказва бъдещ резултат."
)

MODE_LABELS = PREFERENCE_LABELS


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _clean_number(value: Any) -> int | None:
    try:
        number = int(value)
    except Exception:
        return None
    if MIN_NUMBER <= number <= MAX_NUMBER:
        return number
    return None


def _clean_combination(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    numbers: list[int] = []
    for value in values:
        number = _clean_number(value)
        if number is not None:
            numbers.append(number)
    unique = sorted(set(numbers))
    return unique if len(unique) == DRAW_SIZE else []


def _clean_combinations(values: Any) -> list[list[int]]:
    if not isinstance(values, list):
        return []
    result: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for item in values:
        combo = _clean_combination(item)
        key = tuple(combo)
        if combo and key not in seen:
            seen.add(key)
            result.append(combo)
    return result


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def _draw_key(event: dict[str, Any]) -> str:
    pieces = [
        str(event.get("draw_event_id", "") or ""),
        str(event.get("year", "") or ""),
        str(event.get("drawing_no", "") or event.get("draw_number", "") or ""),
        str(event.get("date", "") or ""),
        _numbers_text(event.get("numbers", []) or []),
    ]
    return "|".join(pieces)


def load_latest_draw() -> dict[str, Any]:
    if not CANONICAL_DRAWS_PATH.exists():
        return {}
    rows: list[dict[str, Any]] = []
    with CANONICAL_DRAWS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for index, row in enumerate(reader, start=1):
            numbers = []
            for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
                number = _clean_number(row.get(key))
                if number is not None:
                    numbers.append(number)
            if len(set(numbers)) != DRAW_SIZE:
                continue
            event = {
                "event_index": index,
                "draw_event_id": row.get("draw_event_id", ""),
                "year": row.get("year", ""),
                "draw_number": row.get("draw_number", ""),
                "drawing_no": row.get("drawing_no", ""),
                "date": row.get("date", ""),
                "source": row.get("source", ""),
                "numbers": sorted(numbers),
                "numbers_text": _numbers_text(sorted(numbers)),
            }
            event["draw_key"] = _draw_key(event)
            rows.append(event)
    return rows[-1] if rows else {}


def load_active_plan() -> dict[str, Any]:
    return _read_json(ACTIVE_PLAN_PATH)


def _plan_from_advice(advice: dict[str, Any], *, note_bg: str = "") -> dict[str, Any]:
    rec = advice.get("recommendation", {}) or {}
    latest = load_latest_draw()
    combinations = _clean_combinations(rec.get("combinations", []) or [])
    created_at = _now_iso()
    plan_id = "v94_active_" + created_at.replace("-", "").replace(":", "").replace("+", "Z")
    plan = {
        "step": 94,
        "plan_id": plan_id,
        "status": "ACTIVE",
        "created_at_utc": created_at,
        "note_bg": note_bg,
        "budget_eur": float(advice.get("budget_eur", 0.0) or 0.0),
        "price_per_combination_eur": float(advice.get("price_per_combination_eur", 0.0) or 0.0),
        "max_budget_combinations": int(advice.get("max_budget_combinations", 0) or 0),
        "preference": str(advice.get("preference", "auto") or "auto"),
        "preference_label": str(advice.get("preference_label", "Автоматичен избор") or "Автоматичен избор"),
        "strategy_label": str(rec.get("strategy_label", "") or ""),
        "strategy_type": str(rec.get("strategy_type", "") or ""),
        "source_label": str(rec.get("source_label", "") or ""),
        "combination_count": len(combinations),
        "cost_eur": float(rec.get("cost_eur", 0.0) or 0.0),
        "remaining_budget_eur": float(rec.get("remaining_budget_eur", 0.0) or 0.0),
        "unique_covered_numbers": int(rec.get("unique_covered_numbers", 0) or 0),
        "core_numbers": rec.get("core_numbers", []) or [],
        "core_numbers_text": str(rec.get("core_numbers_text", "") or ""),
        "advisor_score": float(rec.get("advisor_score", 0.0) or 0.0),
        "historical_average_best_hits": float(rec.get("historical_average_best_hits", 0.0) or 0.0),
        "historical_empty_rate_percent": float(rec.get("historical_empty_rate_percent", 0.0) or 0.0),
        "historical_at_least_3_percent": float(rec.get("historical_at_least_3_percent", 0.0) or 0.0),
        "historical_at_least_4_percent": float(rec.get("historical_at_least_4_percent", 0.0) or 0.0),
        "combinations": combinations,
        "saved_after_draw": latest,
        "saved_after_draw_key": latest.get("draw_key", ""),
        "safe_note_bg": SAFE_NOTE_BG,
    }
    return plan


def append_plan_history(plan: dict[str, Any]) -> None:
    HISTORY_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    exists = HISTORY_CSV_PATH.exists()
    fieldnames = [
        "plan_id",
        "created_at_utc",
        "status",
        "budget_eur",
        "price_per_combination_eur",
        "strategy_type",
        "strategy_label",
        "combination_count",
        "cost_eur",
        "unique_covered_numbers",
        "advisor_score",
        "saved_after_draw_year",
        "saved_after_draw_number",
        "saved_after_draw_date",
        "note_bg",
    ]
    latest = plan.get("saved_after_draw", {}) or {}
    row = {
        "plan_id": plan.get("plan_id", ""),
        "created_at_utc": plan.get("created_at_utc", ""),
        "status": plan.get("status", ""),
        "budget_eur": plan.get("budget_eur", 0.0),
        "price_per_combination_eur": plan.get("price_per_combination_eur", 0.0),
        "strategy_type": plan.get("strategy_type", ""),
        "strategy_label": plan.get("strategy_label", ""),
        "combination_count": plan.get("combination_count", 0),
        "cost_eur": plan.get("cost_eur", 0.0),
        "unique_covered_numbers": plan.get("unique_covered_numbers", 0),
        "advisor_score": plan.get("advisor_score", 0.0),
        "saved_after_draw_year": latest.get("year", ""),
        "saved_after_draw_number": latest.get("drawing_no") or latest.get("draw_number") or "",
        "saved_after_draw_date": latest.get("date", ""),
        "note_bg": plan.get("note_bg", ""),
    }
    with HISTORY_CSV_PATH.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def save_active_plan_from_advice(advice: dict[str, Any], *, note_bg: str = "") -> dict[str, Any]:
    plan = _plan_from_advice(advice, note_bg=note_bg)
    _write_json(ACTIVE_PLAN_PATH, plan)
    append_plan_history(plan)
    return plan


def save_active_plan_from_budget(
    budget_eur: float = 10.0,
    price_per_combination: float = DEFAULT_PRICE_PER_COMBINATION,
    preference: str = "auto",
    *,
    note_bg: str = "",
) -> dict[str, Any]:
    advice = build_budget_advice(budget_eur, price_per_combination, preference)
    return save_active_plan_from_advice(advice, note_bg=note_bg)


def evaluate_plan_against_latest(plan: dict[str, Any], *, allow_same_draw: bool = False) -> dict[str, Any]:
    if not plan:
        return {"status": "NO_ACTIVE_PLAN", "message_bg": "Няма запазен активен план."}
    latest = load_latest_draw()
    if not latest:
        return {"status": "NO_DRAW_DATA", "message_bg": "Няма наличен последен тираж за проверка."}

    saved_key = str(plan.get("saved_after_draw_key", "") or "")
    latest_key = str(latest.get("draw_key", "") or "")
    if saved_key and latest_key == saved_key and not allow_same_draw:
        return {
            "status": "WAITING_NEXT_DRAW",
            "message_bg": "Планът е запазен след текущия последен тираж. Изчакай следващ реален тираж или използвай демо проверка.",
            "active_plan": plan,
            "latest_draw": latest,
            "saved_after_draw": plan.get("saved_after_draw", {}) or {},
            "rows": [],
        }

    actual = set(latest.get("numbers", []) or [])
    rows: list[dict[str, Any]] = []
    for index, combo in enumerate(_clean_combinations(plan.get("combinations", []) or []), start=1):
        hits = sorted(set(combo).intersection(actual))
        misses = sorted(set(combo).difference(actual))
        rows.append(
            {
                "combination_index": index,
                "numbers": _numbers_text(combo),
                "hit_count": len(hits),
                "matching_numbers": _numbers_text(hits),
                "missing_numbers": _numbers_text(misses),
                "is_empty": len(hits) == 0,
                "has_3_plus": len(hits) >= 3,
                "has_4_plus": len(hits) >= 4,
            }
        )

    best_hit_count = max((int(row["hit_count"]) for row in rows), default=0)
    best_rows = [row for row in rows if int(row["hit_count"]) == best_hit_count]
    total_hits = sum(int(row["hit_count"]) for row in rows)
    rows_with_hits = sum(1 for row in rows if int(row["hit_count"]) > 0)
    rows_with_3_plus = sum(1 for row in rows if int(row["hit_count"]) >= 3)
    rows_with_4_plus = sum(1 for row in rows if int(row["hit_count"]) >= 4)
    plan_empty = best_hit_count == 0

    expected_avg = float(plan.get("historical_average_best_hits", 0.0) or 0.0)
    if best_hit_count > expected_avg + 0.25:
        verdict = "Над историческия профил"
    elif best_hit_count + 0.25 < expected_avg:
        verdict = "Под историческия профил"
    else:
        verdict = "Близо до историческия профил"

    result = {
        "status": "EVALUATED",
        "message_bg": "Планът е проверен срещу най-новия наличен тираж.",
        "evaluation_time_utc": _now_iso(),
        "active_plan": plan,
        "latest_draw": latest,
        "saved_after_draw": plan.get("saved_after_draw", {}) or {},
        "rows": rows,
        "summary": {
            "plan_id": plan.get("plan_id", ""),
            "latest_draw_year": latest.get("year", ""),
            "latest_draw_number": latest.get("drawing_no") or latest.get("draw_number") or "",
            "latest_draw_date": latest.get("date", ""),
            "latest_draw_numbers": latest.get("numbers_text", ""),
            "combination_count": len(rows),
            "best_hit_count": best_hit_count,
            "best_combination_indexes": [row["combination_index"] for row in best_rows],
            "best_matching_numbers": best_rows[0]["matching_numbers"] if best_rows else "",
            "total_hits_across_rows": total_hits,
            "rows_with_hits": rows_with_hits,
            "rows_with_3_plus": rows_with_3_plus,
            "rows_with_4_plus": rows_with_4_plus,
            "plan_empty": plan_empty,
            "historical_average_best_hits": expected_avg,
            "historical_empty_rate_percent": float(plan.get("historical_empty_rate_percent", 0.0) or 0.0),
            "verdict_bg": verdict,
        },
    }
    return result


def _write_result_csv(result: dict[str, Any]) -> None:
    LATEST_RESULT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["combination_index", "numbers", "hit_count", "matching_numbers", "missing_numbers", "is_empty", "has_3_plus", "has_4_plus"]
    with LATEST_RESULT_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.get("rows", []) or []:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def build_active_plan_tracker_model() -> dict[str, Any]:
    active_plan = load_active_plan()
    created_reference = False
    if not active_plan:
        active_plan = save_active_plan_from_budget(
            10.0,
            DEFAULT_PRICE_PER_COMBINATION,
            "auto",
            note_bg="Автоматично създаден референтен план от Step 93 при build на Step 94.",
        )
        created_reference = True

    result = evaluate_plan_against_latest(active_plan, allow_same_draw=False)
    demo_result = evaluate_plan_against_latest(active_plan, allow_same_draw=True)
    _write_result_csv(demo_result if demo_result.get("rows") else result)

    model = {
        "step": 94,
        "status": "OK",
        "title_bg": "План и резултат",
        "safe_note_bg": SAFE_NOTE_BG,
        "created_reference_plan": created_reference,
        "active_plan_path": str(ACTIVE_PLAN_PATH.relative_to(ROOT)),
        "history_path": str(HISTORY_CSV_PATH.relative_to(ROOT)),
        "latest_result_path": str(LATEST_RESULT_CSV_PATH.relative_to(ROOT)),
        "active_plan": active_plan,
        "result": result,
        "demo_result": demo_result,
        "method_summary_bg": (
            "Step 94 заключва бюджетния план към последния наличен тираж в момента на запазване. "
            "Когато бъде добавен нов тираж, модулът сравнява активните комбинации с новите числа и показва реален резултат."
        ),
    }
    return model


def save_active_plan_tracker_outputs(model: dict[str, Any]) -> None:
    _write_json(MODEL_PATH, model)
    _write_json(SUMMARY_JSON_PATH, {
        "step": 94,
        "status": model.get("status", "UNKNOWN"),
        "title_bg": model.get("title_bg", "План и резултат"),
        "active_plan_id": (model.get("active_plan", {}) or {}).get("plan_id", ""),
        "strategy_type": (model.get("active_plan", {}) or {}).get("strategy_type", ""),
        "strategy_label": (model.get("active_plan", {}) or {}).get("strategy_label", ""),
        "budget_eur": (model.get("active_plan", {}) or {}).get("budget_eur", 0.0),
        "combination_count": (model.get("active_plan", {}) or {}).get("combination_count", 0),
        "cost_eur": (model.get("active_plan", {}) or {}).get("cost_eur", 0.0),
        "result_status": (model.get("result", {}) or {}).get("status", ""),
        "demo_best_hit_count": ((model.get("demo_result", {}) or {}).get("summary", {}) or {}).get("best_hit_count", 0),
        "safe_note_bg": SAFE_NOTE_BG,
    })

    plan = model.get("active_plan", {}) or {}
    result = model.get("result", {}) or {}
    demo = model.get("demo_result", {}) or {}
    lines = [
        "# План и резултат",
        "",
        f"- Активен план: **{plan.get('strategy_label', '-')}**",
        f"- Тип: **{plan.get('strategy_type', '-')}**",
        f"- Бюджет: **{float(plan.get('budget_eur', 0.0)):.2f} EUR**",
        f"- Комбинации: **{int(plan.get('combination_count', 0))}**",
        f"- Цена: **{float(plan.get('cost_eur', 0.0)):.2f} EUR**",
        f"- Статус на реална проверка: **{result.get('status', '-')}**",
        f"- Демо най-добри попадения срещу последния наличен тираж: **{((demo.get('summary', {}) or {}).get('best_hit_count', 0))}**",
        "",
        SAFE_NOTE_BG,
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    model = build_active_plan_tracker_model()
    save_active_plan_tracker_outputs(model)
    return model


if __name__ == "__main__":
    payload = build_and_save()
    plan = payload.get("active_plan", {}) or {}
    result = payload.get("result", {}) or {}
    demo = payload.get("demo_result", {}) or {}
    print("STEP_94_STATUS", payload.get("status", "UNKNOWN"))
    print("ACTIVE_PLAN", plan.get("strategy_type", "-"), plan.get("combination_count", 0), f"{float(plan.get('cost_eur', 0.0)):.2f}")
    print("RESULT_STATUS", result.get("status", "-"))
    print("DEMO_BEST_HITS", ((demo.get("summary", {}) or {}).get("best_hit_count", 0)))
