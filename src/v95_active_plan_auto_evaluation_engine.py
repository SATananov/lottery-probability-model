from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v94_active_budget_plan_tracker_engine import load_active_plan, load_latest_draw

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "v95" / "v95_active_plan_auto_evaluation_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v95_active_plan_auto_evaluation_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v95_active_plan_auto_evaluation_summary.md"
HISTORY_CSV_PATH = ROOT / "reports" / "v95_active_plan_auto_evaluation_history.csv"
LATEST_RESULT_CSV_PATH = ROOT / "reports" / "v95_active_plan_auto_evaluation_latest_result.csv"
V94_LATEST_RESULT_CSV_PATH = ROOT / "reports" / "v94_latest_plan_result.csv"

DRAW_SIZE = 6
MIN_NUMBER = 1
MAX_NUMBER = 49

SAFE_NOTE_V95_BG = (
    "Step 95 проверява активния бюджетен план срещу числата, въведени в Добавяне на тираж, "
    "преди новият тираж да обнови dataset-а. Това е отчет на вече запазен план, не гаранция за печалба."
)

RESULT_FIELDS = [
    "combination_index",
    "numbers",
    "hit_count",
    "matching_numbers",
    "missing_numbers",
    "is_empty",
    "has_3_plus",
    "has_4_plus",
]

HISTORY_FIELDS = [
    "evaluated_at_utc",
    "source",
    "plan_id",
    "evaluated_draw_key",
    "draw_date",
    "draw_number",
    "draw_position",
    "draw_numbers",
    "combination_count",
    "best_hit_count",
    "best_combination_indexes",
    "best_matching_numbers",
    "total_hits_across_rows",
    "rows_with_hits",
    "rows_with_3_plus",
    "rows_with_4_plus",
    "verdict_bg",
    "status",
    "safe_note_bg",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _clean_number(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if MIN_NUMBER <= number <= MAX_NUMBER:
        return number
    return None


def normalize_draw_numbers(values: list[Any]) -> list[int]:
    numbers: list[int] = []
    for value in values:
        number = _clean_number(value)
        if number is not None:
            numbers.append(number)
    clean = sorted(set(numbers))
    if len(clean) != DRAW_SIZE:
        raise ValueError("Очакват се точно 6 различни числа между 1 и 49.")
    return clean


def _clean_combination(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    numbers: list[int] = []
    for value in values:
        number = _clean_number(value)
        if number is not None:
            numbers.append(number)
    clean = sorted(set(numbers))
    return clean if len(clean) == DRAW_SIZE else []


def _clean_combinations(values: Any) -> list[list[int]]:
    if not isinstance(values, list):
        return []
    combos: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for item in values:
        combo = _clean_combination(item)
        key = tuple(combo)
        if combo and key not in seen:
            seen.add(key)
            combos.append(combo)
    return combos


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text.replace(",", ".")))
    except (TypeError, ValueError):
        return default


def _sort_tuple(event: dict[str, Any]) -> tuple[str, int, int, int]:
    return (
        str(event.get("date", "") or ""),
        _as_int(event.get("year"), 0),
        _as_int(event.get("draw_number") or event.get("draw_no"), 0),
        _as_int(event.get("drawing_no") or event.get("draw_position"), 0),
    )


def _draw_key(event: dict[str, Any]) -> str:
    pieces = [
        str(event.get("draw_event_id", "") or ""),
        str(event.get("year", "") or ""),
        str(event.get("drawing_no") or event.get("draw_position") or ""),
        str(event.get("date", "") or ""),
        _numbers_text(event.get("numbers", []) or []),
    ]
    return "|".join(pieces)


def build_pending_draw_event(
    numbers: list[Any],
    *,
    draw_date: str,
    year: int,
    draw_no: int,
    draw_position: int = 1,
    source: str = "add_draw_pre_save",
) -> dict[str, Any]:
    clean = normalize_draw_numbers(numbers)
    event = {
        "event_index": "pending_add_draw",
        "draw_event_id": f"pending-{year}-{draw_no}-{draw_position}",
        "year": str(year),
        "draw_number": str(draw_no),
        "drawing_no": str(draw_position),
        "date": str(draw_date),
        "source": source,
        "numbers": clean,
        "numbers_text": _numbers_text(clean),
    }
    event["draw_key"] = _draw_key(event)
    return event


def _is_draw_after_saved(plan: dict[str, Any], event: dict[str, Any]) -> bool:
    saved = plan.get("saved_after_draw", {}) or {}
    if not saved:
        return True
    return _sort_tuple(event) > _sort_tuple(saved)


def _history_has_draw(plan_id: str, draw_key: str) -> bool:
    for row in _read_csv(HISTORY_CSV_PATH):
        if row.get("plan_id") == plan_id and row.get("evaluated_draw_key") == draw_key:
            return True
    return False


def _waiting_result(plan: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "WAITING_NEXT_DRAW",
        "message_bg": "Активният бюджетен план чака следващ реален тираж. Последният наличен тираж все още не е след плана.",
        "active_plan": plan,
        "draw": event,
        "saved_after_draw": plan.get("saved_after_draw", {}) or {},
        "rows": [],
        "safe_note_bg": SAFE_NOTE_V95_BG,
    }


def evaluate_active_plan_against_draw_event(
    event: dict[str, Any],
    *,
    persist: bool = False,
    source: str = "add_draw_pre_save",
) -> dict[str, Any]:
    plan = load_active_plan()
    if not plan:
        return {
            "status": "NO_ACTIVE_PLAN",
            "message_bg": "Няма активен бюджетен план за проверка.",
            "draw": event,
            "rows": [],
            "safe_note_bg": SAFE_NOTE_V95_BG,
        }

    if not _is_draw_after_saved(plan, event):
        return {
            "status": "DRAW_NOT_AFTER_ACTIVE_PLAN",
            "message_bg": "Въведеният тираж не е след тиража, към който е заключен активният план. Реална проверка не се записва, за да няма backfit.",
            "active_plan": plan,
            "draw": event,
            "saved_after_draw": plan.get("saved_after_draw", {}) or {},
            "rows": [],
            "safe_note_bg": SAFE_NOTE_V95_BG,
        }

    actual = set(event.get("numbers", []) or [])
    rows: list[dict[str, Any]] = []
    for index, combo in enumerate(_clean_combinations(plan.get("combinations", []) or []), start=1):
        hits = sorted(set(combo).intersection(actual))
        misses = sorted(set(combo).difference(actual))
        rows.append({
            "combination_index": index,
            "numbers": _numbers_text(combo),
            "hit_count": len(hits),
            "matching_numbers": _numbers_text(hits),
            "missing_numbers": _numbers_text(misses),
            "is_empty": len(hits) == 0,
            "has_3_plus": len(hits) >= 3,
            "has_4_plus": len(hits) >= 4,
        })

    best_hit_count = max((int(row["hit_count"]) for row in rows), default=0)
    best_rows = [row for row in rows if int(row["hit_count"]) == best_hit_count]
    total_hits = sum(int(row["hit_count"]) for row in rows)
    rows_with_hits = sum(1 for row in rows if int(row["hit_count"]) > 0)
    rows_with_3_plus = sum(1 for row in rows if int(row["hit_count"]) >= 3)
    rows_with_4_plus = sum(1 for row in rows if int(row["hit_count"]) >= 4)

    expected_avg = float(plan.get("historical_average_best_hits", 0.0) or 0.0)
    if best_hit_count > expected_avg + 0.25:
        verdict = "Над историческия профил"
    elif best_hit_count + 0.25 < expected_avg:
        verdict = "Под историческия профил"
    else:
        verdict = "Близо до историческия профил"

    result = {
        "step": 95,
        "status": "EVALUATED",
        "message_bg": "Активният бюджетен план е проверен срещу въведения нов тираж преди обновяване на dataset-а.",
        "evaluation_type": "ADD_DRAW_PRE_SAVE_REAL_RESULT",
        "evaluated_at_utc": _now_iso(),
        "evaluated_draw_key": event.get("draw_key", ""),
        "source": source,
        "active_plan": plan,
        "draw": event,
        "saved_after_draw": plan.get("saved_after_draw", {}) or {},
        "rows": rows,
        "summary": {
            "plan_id": plan.get("plan_id", ""),
            "draw_year": event.get("year", ""),
            "draw_number": event.get("draw_number", ""),
            "draw_position": event.get("drawing_no", ""),
            "draw_date": event.get("date", ""),
            "draw_numbers": event.get("numbers_text", ""),
            "combination_count": len(rows),
            "best_hit_count": best_hit_count,
            "best_combination_indexes": [row["combination_index"] for row in best_rows],
            "best_matching_numbers": best_rows[0]["matching_numbers"] if best_rows else "",
            "total_hits_across_rows": total_hits,
            "rows_with_hits": rows_with_hits,
            "rows_with_3_plus": rows_with_3_plus,
            "rows_with_4_plus": rows_with_4_plus,
            "historical_average_best_hits": expected_avg,
            "historical_empty_rate_percent": float(plan.get("historical_empty_rate_percent", 0.0) or 0.0),
            "verdict_bg": verdict,
        },
        "safe_note_bg": SAFE_NOTE_V95_BG,
    }

    if persist:
        already_recorded = _history_has_draw(plan.get("plan_id", ""), event.get("draw_key", ""))
        save_outputs(result, persist_to_v94=True, append_history=not already_recorded)
        result["already_recorded"] = already_recorded

    return result


def evaluate_active_plan_against_pending_draw(
    numbers: list[Any],
    *,
    draw_date: str,
    year: int,
    draw_no: int,
    draw_position: int = 1,
    persist: bool = False,
    source: str = "add_draw_pre_save",
) -> dict[str, Any]:
    event = build_pending_draw_event(
        numbers,
        draw_date=draw_date,
        year=year,
        draw_no=draw_no,
        draw_position=draw_position,
        source=source,
    )
    return evaluate_active_plan_against_draw_event(event, persist=persist, source=source)


def _history_row(result: dict[str, Any]) -> dict[str, Any]:
    plan = result.get("active_plan", {}) or {}
    draw = result.get("draw", {}) or {}
    summary = result.get("summary", {}) or {}
    return {
        "evaluated_at_utc": result.get("evaluated_at_utc", ""),
        "source": result.get("source", ""),
        "plan_id": plan.get("plan_id", ""),
        "evaluated_draw_key": result.get("evaluated_draw_key", ""),
        "draw_date": draw.get("date", ""),
        "draw_number": draw.get("draw_number", ""),
        "draw_position": draw.get("drawing_no", ""),
        "draw_numbers": draw.get("numbers_text", ""),
        "combination_count": summary.get("combination_count", 0),
        "best_hit_count": summary.get("best_hit_count", 0),
        "best_combination_indexes": ",".join(str(item) for item in summary.get("best_combination_indexes", []) or []),
        "best_matching_numbers": summary.get("best_matching_numbers", ""),
        "total_hits_across_rows": summary.get("total_hits_across_rows", 0),
        "rows_with_hits": summary.get("rows_with_hits", 0),
        "rows_with_3_plus": summary.get("rows_with_3_plus", 0),
        "rows_with_4_plus": summary.get("rows_with_4_plus", 0),
        "verdict_bg": summary.get("verdict_bg", ""),
        "status": result.get("status", ""),
        "safe_note_bg": SAFE_NOTE_V95_BG,
    }


def save_outputs(result: dict[str, Any], *, persist_to_v94: bool = False, append_history: bool = False) -> None:
    _write_json(MODEL_PATH, {
        "step": 95,
        "status": result.get("status", "UNKNOWN"),
        "title_bg": "Автоматична проверка на активния план",
        "result": result,
        "safe_note_bg": SAFE_NOTE_V95_BG,
    })
    _write_json(SUMMARY_JSON_PATH, {
        "step": 95,
        "status": result.get("status", "UNKNOWN"),
        "evaluation_type": result.get("evaluation_type", ""),
        "plan_id": ((result.get("active_plan", {}) or {}).get("plan_id", "")),
        "draw_key": result.get("evaluated_draw_key", ""),
        "best_hit_count": ((result.get("summary", {}) or {}).get("best_hit_count", 0)),
        "rows_with_3_plus": ((result.get("summary", {}) or {}).get("rows_with_3_plus", 0)),
        "rows_with_4_plus": ((result.get("summary", {}) or {}).get("rows_with_4_plus", 0)),
        "message_bg": result.get("message_bg", ""),
        "safe_note_bg": SAFE_NOTE_V95_BG,
    })

    rows = result.get("rows", []) or []
    _write_csv(LATEST_RESULT_CSV_PATH, rows, RESULT_FIELDS)
    if persist_to_v94 and result.get("status") == "EVALUATED":
        _write_csv(V94_LATEST_RESULT_CSV_PATH, rows, RESULT_FIELDS)
    if append_history and result.get("status") == "EVALUATED":
        _append_csv(HISTORY_CSV_PATH, _history_row(result), HISTORY_FIELDS)

    draw = result.get("draw", {}) or {}
    summary = result.get("summary", {}) or {}
    lines = [
        "# Step 95 — Автоматична проверка на активния план",
        "",
        result.get("message_bg", ""),
        "",
        f"- Статус: **{result.get('status', 'UNKNOWN')}**",
        f"- Тираж: **{draw.get('year', '')} / {draw.get('draw_number', '')} / теглене {draw.get('drawing_no', '')}**",
        f"- Числа: **{draw.get('numbers_text', '')}**",
        f"- Най-добра комбинация: **{summary.get('best_hit_count', 0)} попадения**",
        f"- Комбинации 3+: **{summary.get('rows_with_3_plus', 0)}**",
        f"- Комбинации 4+: **{summary.get('rows_with_4_plus', 0)}**",
        "",
        SAFE_NOTE_V95_BG,
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_active_plan_auto_evaluation_model() -> dict[str, Any]:
    latest = load_latest_draw()
    plan = load_active_plan()
    if not latest:
        result = {"status": "NO_DRAW_DATA", "message_bg": "Няма наличен последен тираж за автоматична проверка.", "rows": [], "safe_note_bg": SAFE_NOTE_V95_BG}
    elif not plan:
        result = {"status": "NO_ACTIVE_PLAN", "message_bg": "Няма активен бюджетен план за проверка.", "draw": latest, "rows": [], "safe_note_bg": SAFE_NOTE_V95_BG}
    elif not _is_draw_after_saved(plan, latest):
        result = _waiting_result(plan, latest)
    else:
        result = evaluate_active_plan_against_draw_event(latest, persist=False, source="v95_build_latest_canonical")
    save_outputs(result, persist_to_v94=result.get("status") == "EVALUATED", append_history=False)
    return result


def build_and_save() -> dict[str, Any]:
    return build_active_plan_auto_evaluation_model()


if __name__ == "__main__":
    payload = build_and_save()
    summary = payload.get("summary", {}) or {}
    print("STEP_95_STATUS", payload.get("status", "UNKNOWN"))
    print("EVALUATION_TYPE", payload.get("evaluation_type", "-"))
    print("BEST_HITS", summary.get("best_hit_count", 0))
