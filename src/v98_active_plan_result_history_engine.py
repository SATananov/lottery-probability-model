from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v98" / "v98_active_plan_result_history_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v98_active_plan_result_history_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v98_active_plan_result_history_summary.md"
HISTORY_CSV_PATH = ROOT / "reports" / "v98_active_plan_result_history.csv"
PLAN_SUMMARY_CSV_PATH = ROOT / "reports" / "v98_active_plan_summary.csv"

V94_MODEL_PATH = ROOT / "models" / "v94" / "v94_active_budget_plan_tracker_model.json"
V95_MODEL_PATH = ROOT / "models" / "v95" / "v95_active_plan_auto_evaluation_model.json"
V95_HISTORY_CSV_PATH = ROOT / "reports" / "v95_active_plan_auto_evaluation_history.csv"
V95_LATEST_RESULT_CSV_PATH = ROOT / "reports" / "v95_active_plan_auto_evaluation_latest_result.csv"

SAFE_NOTE_BG = (
    "Step 98 е исторически дневник на вече запазени активни планове и реални резултати. "
    "Той не добавя нова прогноза, не променя математиката и не обещава печалба."
)

HISTORY_FIELDS = [
    "evaluated_at_utc",
    "plan_id",
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
    "performance_bucket_bg",
]

PLAN_SUMMARY_FIELDS = [
    "plan_id",
    "status",
    "strategy_type",
    "combination_count",
    "cost_eur",
    "cost_text",
    "saved_after_draw_date",
    "saved_after_draw_numbers",
    "v95_status",
    "real_result_rows",
    "best_hit_count_max",
    "best_hit_count_average",
    "rows_with_3_plus_rate_percent",
    "rows_with_4_plus_rate_percent",
    "latest_result_date",
    "latest_verdict_bg",
    "next_status_bg",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _as_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text.replace(",", ".")))
    except Exception:
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text.replace(",", "."))
    except Exception:
        return default


def _format_float(value: float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def _find_active_plan(v94_payload: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        v94_payload.get("active_plan", {}),
        (v94_payload.get("result", {}) or {}).get("active_plan", {}),
        (v94_payload.get("demo_result", {}) or {}).get("active_plan", {}),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("plan_id"):
            return candidate
    return {}


def _v95_status(v95_payload: dict[str, Any]) -> str:
    result = v95_payload.get("result", {}) if isinstance(v95_payload.get("result", {}), dict) else {}
    return str(v95_payload.get("status") or result.get("status") or "UNKNOWN")


def _performance_bucket(best_hit_count: int) -> str:
    if best_hit_count >= 5:
        return "Много силен резултат"
    if best_hit_count == 4:
        return "Силен резултат"
    if best_hit_count == 3:
        return "Добър сигнал"
    if best_hit_count == 2:
        return "Нормален резултат"
    if best_hit_count == 1:
        return "Слаб резултат"
    return "Празен резултат"


def _normalize_history_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        plan_id = str(row.get("plan_id", "")).strip()
        draw_key = str(row.get("evaluated_draw_key", "")).strip()
        dedupe_key = (plan_id, draw_key or str(row.get("draw_date", "")))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        best_hit_count = _as_int(row.get("best_hit_count"), 0)
        normalized.append({
            "evaluated_at_utc": row.get("evaluated_at_utc", ""),
            "plan_id": plan_id,
            "draw_date": row.get("draw_date", ""),
            "draw_number": row.get("draw_number", ""),
            "draw_position": row.get("draw_position", ""),
            "draw_numbers": row.get("draw_numbers", ""),
            "combination_count": _as_int(row.get("combination_count"), 0),
            "best_hit_count": best_hit_count,
            "best_combination_indexes": row.get("best_combination_indexes", ""),
            "best_matching_numbers": row.get("best_matching_numbers", ""),
            "total_hits_across_rows": _as_int(row.get("total_hits_across_rows"), 0),
            "rows_with_hits": _as_int(row.get("rows_with_hits"), 0),
            "rows_with_3_plus": _as_int(row.get("rows_with_3_plus"), 0),
            "rows_with_4_plus": _as_int(row.get("rows_with_4_plus"), 0),
            "verdict_bg": row.get("verdict_bg", ""),
            "status": row.get("status", ""),
            "performance_bucket_bg": _performance_bucket(best_hit_count),
        })
    normalized.sort(key=lambda item: (str(item.get("draw_date", "")), str(item.get("draw_number", "")), str(item.get("draw_position", ""))))
    return normalized


def _summarize_history(rows: list[dict[str, Any]]) -> dict[str, Any]:
    best_values = [_as_int(row.get("best_hit_count"), 0) for row in rows]
    row_count = len(rows)
    if not rows:
        return {
            "real_result_rows": 0,
            "best_hit_count_max": 0,
            "best_hit_count_average": 0.0,
            "rows_with_3_plus_count": 0,
            "rows_with_4_plus_count": 0,
            "rows_with_3_plus_rate_percent": 0.0,
            "rows_with_4_plus_rate_percent": 0.0,
            "latest_result_date": "",
            "latest_verdict_bg": "",
            "trend_bg": "Още няма реални резултати",
        }

    rows_with_3_plus = sum(1 for row in rows if _as_int(row.get("rows_with_3_plus"), 0) > 0)
    rows_with_4_plus = sum(1 for row in rows if _as_int(row.get("rows_with_4_plus"), 0) > 0)
    latest = rows[-1]
    trend = "Нужни са още реални резултати за тренд"
    if len(best_values) >= 3:
        first_window = mean(best_values[:3])
        last_window = mean(best_values[-3:])
        if last_window > first_window + 0.2:
            trend = "Последните резултати са по-силни"
        elif last_window + 0.2 < first_window:
            trend = "Последните резултати са по-слаби"
        else:
            trend = "Трендът е стабилен"

    return {
        "real_result_rows": row_count,
        "best_hit_count_max": max(best_values),
        "best_hit_count_average": round(mean(best_values), 6),
        "rows_with_3_plus_count": rows_with_3_plus,
        "rows_with_4_plus_count": rows_with_4_plus,
        "rows_with_3_plus_rate_percent": round(rows_with_3_plus / row_count * 100.0, 6),
        "rows_with_4_plus_rate_percent": round(rows_with_4_plus / row_count * 100.0, 6),
        "latest_result_date": latest.get("draw_date", ""),
        "latest_verdict_bg": latest.get("verdict_bg", ""),
        "trend_bg": trend,
    }


def build_active_plan_result_history() -> dict[str, Any]:
    v94_payload = _read_json(V94_MODEL_PATH)
    v95_payload = _read_json(V95_MODEL_PATH)
    active_plan = _find_active_plan(v94_payload)
    v95_status = _v95_status(v95_payload)
    history_rows = _normalize_history_rows(_read_csv(V95_HISTORY_CSV_PATH))
    history_summary = _summarize_history(history_rows)

    plan_saved_after = active_plan.get("saved_after_draw", {}) if isinstance(active_plan.get("saved_after_draw", {}), dict) else {}
    cost = _as_float(active_plan.get("cost_eur") or active_plan.get("estimated_cost_eur"), 0.0)
    plan_summary = {
        "plan_id": active_plan.get("plan_id", ""),
        "status": active_plan.get("status", ""),
        "strategy_type": active_plan.get("strategy_type") or active_plan.get("recommended_type") or "",
        "combination_count": _as_int(active_plan.get("combination_count") or len(active_plan.get("combinations", []) or []), 0),
        "cost_eur": round(cost, 2),
        "cost_text": f"{cost:.2f}",
        "saved_after_draw_date": plan_saved_after.get("date", ""),
        "saved_after_draw_numbers": plan_saved_after.get("numbers_text", ""),
        "v95_status": v95_status,
        **history_summary,
    }

    if not active_plan:
        status = "NO_ACTIVE_PLAN"
        next_status_bg = "Няма активен план за проследяване."
    elif history_rows:
        status = "HAS_HISTORY"
        next_status_bg = "Историята има реални резултати. След следващ тираж ще се добави нов ред."
    elif v95_status == "WAITING_NEXT_DRAW":
        status = "WAITING_NEXT_DRAW"
        next_status_bg = "Активният план е готов, но още няма следващ реален тираж след заключването му."
    else:
        status = "READY"
        next_status_bg = "Историята е подготвена. Реален ред ще се появи след първата честна Step 95 оценка."

    plan_summary["next_status_bg"] = next_status_bg

    payload = {
        "step": 98,
        "status": status,
        "title_bg": "История на резултатите от активния план",
        "generated_at_utc": _now_iso(),
        "active_plan": plan_summary,
        "history_summary": history_summary,
        "history_rows": history_rows,
        "source_files": {
            "active_plan_model": V94_MODEL_PATH.relative_to(ROOT).as_posix(),
            "step95_model": V95_MODEL_PATH.relative_to(ROOT).as_posix(),
            "step95_history": V95_HISTORY_CSV_PATH.relative_to(ROOT).as_posix(),
            "step95_latest_result": V95_LATEST_RESULT_CSV_PATH.relative_to(ROOT).as_posix(),
        },
        "method_bg": (
            "Step 98 не изчислява нови числа. Той обобщава само вече записаните Step 95 реални проверки "
            "на активния план и пази отделен dashboard за история, средни стойности, 3+/4+ честота и тренд."
        ),
        "safe_note_bg": SAFE_NOTE_BG,
    }

    _write_csv(HISTORY_CSV_PATH, history_rows, HISTORY_FIELDS)
    _write_csv(PLAN_SUMMARY_CSV_PATH, [plan_summary], PLAN_SUMMARY_FIELDS)
    _write_json(MODEL_PATH, payload)
    _write_json(SUMMARY_JSON_PATH, {
        "step": 98,
        "status": status,
        "plan_id": plan_summary.get("plan_id", ""),
        "strategy_type": plan_summary.get("strategy_type", ""),
        "combination_count": plan_summary.get("combination_count", 0),
        "cost_eur": plan_summary.get("cost_eur", 0.0),
        "v95_status": v95_status,
        "real_result_rows": history_summary.get("real_result_rows", 0),
        "best_hit_count_max": history_summary.get("best_hit_count_max", 0),
        "best_hit_count_average": history_summary.get("best_hit_count_average", 0.0),
        "rows_with_3_plus_rate_percent": history_summary.get("rows_with_3_plus_rate_percent", 0.0),
        "rows_with_4_plus_rate_percent": history_summary.get("rows_with_4_plus_rate_percent", 0.0),
        "next_status_bg": next_status_bg,
        "safe_note_bg": SAFE_NOTE_BG,
    })

    lines = [
        "# Step 98 — История на резултатите от активния план",
        "",
        f"- Статус: **{status}**",
        f"- Активен план: **{plan_summary.get('strategy_type', '-')}** / **{plan_summary.get('combination_count', 0)} комбинации** / **{plan_summary.get('cost_text', '0.00')} EUR**",
        f"- Step 95 статус: **{v95_status}**",
        f"- Реални записи в историята: **{history_summary.get('real_result_rows', 0)}**",
        f"- Максимум най-добри попадения: **{history_summary.get('best_hit_count_max', 0)}**",
        f"- Средно най-добри попадения: **{_format_float(history_summary.get('best_hit_count_average', 0.0), 3)}**",
        f"- Тренд: **{history_summary.get('trend_bg', '-')}**",
        "",
        next_status_bg,
        "",
        SAFE_NOTE_BG,
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def load_active_plan_result_history() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        return build_active_plan_result_history()
    payload = _read_json(MODEL_PATH)
    return payload or build_active_plan_result_history()


def build_and_save() -> dict[str, Any]:
    return build_active_plan_result_history()
