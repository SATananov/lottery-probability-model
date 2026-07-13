from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v100" / "v100_final_release_lock_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v100_final_release_lock_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v100_final_release_lock_summary.md"
CHECKLIST_CSV_PATH = ROOT / "reports" / "v100_final_release_lock_checklist.csv"
MANIFEST_CSV_PATH = ROOT / "reports" / "v100_final_release_lock_manifest.csv"

V94_MODEL_PATH = ROOT / "models" / "v94" / "v94_active_budget_plan_tracker_model.json"
V95_MODEL_PATH = ROOT / "models" / "v95" / "v95_active_plan_auto_evaluation_model.json"
V96_MODEL_PATH = ROOT / "models" / "v96" / "v96_add_draw_controlled_flow_model.json"
V97_MODEL_PATH = ROOT / "models" / "v97" / "v97_real_draw_lifecycle_model.json"
V98_MODEL_PATH = ROOT / "models" / "v98" / "v98_active_plan_result_history_model.json"
V99_MODEL_PATH = ROOT / "models" / "v99" / "v99_final_user_dashboard_model.json"

HISTORICAL_DRAWS_PATH = ROOT / "data" / "historical_draws.csv"
NORMALIZED_DRAWS_PATH = ROOT / "data" / "v40_normalized_draw_events.csv"
CANONICAL_DRAWS_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
STREAMLIT_APP_PATH = ROOT / "streamlit_app.py"
ADD_DRAWS_PATH = ROOT / "src" / "add_draws_section.py"

SAFE_NOTE_BG = (
    "Step 100 е финално заключване на v1 workflow. Той проверява готовността на проекта, "
    "реалния цикъл на тиража, активния план, историята и потребителските действия. "
    "Не добавя прогноза, не променя математиката и не гарантира печалба."
)

CHECKLIST_FIELDS = [
    "area_bg",
    "check_bg",
    "status",
    "blocking",
    "details_bg",
]

MANIFEST_FIELDS = [
    "artifact_type",
    "path",
    "status",
    "note_bg",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


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


def _money(value: Any) -> str:
    return f"{_as_float(value, 0.0):.2f} EUR"


def _numbers_from_row(row: dict[str, Any]) -> list[int]:
    numbers: list[int] = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        number = _as_int(row.get(key), 0)
        if 1 <= number <= 49:
            numbers.append(number)
    return numbers


def _numbers_text(numbers: Any) -> str:
    if isinstance(numbers, str):
        return numbers
    if isinstance(numbers, list):
        return ", ".join(str(item) for item in numbers)
    return ""


def _dataset_snapshot() -> dict[str, Any]:
    historical = _read_csv_rows(HISTORICAL_DRAWS_PATH)
    normalized = _read_csv_rows(NORMALIZED_DRAWS_PATH)
    canonical = _read_csv_rows(CANONICAL_DRAWS_PATH)
    latest = historical[-1] if historical else {}
    latest_numbers = _numbers_from_row(latest)
    return {
        "historical_rows": len(historical),
        "normalized_rows": len(normalized),
        "canonical_rows": len(canonical),
        "latest_draw_date": latest.get("date", ""),
        "latest_draw_year": latest.get("year", ""),
        "latest_draw_no": latest.get("draw_no") or latest.get("draw_number") or "",
        "latest_draw_position": latest.get("draw_position", ""),
        "latest_numbers": latest_numbers,
        "latest_numbers_text": _numbers_text(latest_numbers),
        "datasets_synced": len(historical) == len(normalized) == len(canonical) and len(historical) >= 10058,
    }


def _active_plan(v94: dict[str, Any], v99: dict[str, Any]) -> dict[str, Any]:
    plan99 = v99.get("active_plan", {}) if isinstance(v99.get("active_plan"), dict) else {}
    plan94 = v94.get("active_plan", {}) if isinstance(v94.get("active_plan"), dict) else {}
    source = plan99 or plan94
    return {
        "plan_id": source.get("plan_id", ""),
        "strategy_type": source.get("strategy_type", ""),
        "combination_count": _as_int(source.get("combination_count"), 0),
        "cost_eur": _as_float(source.get("cost_eur"), 0.0),
        "cost_text": _money(source.get("cost_eur", 0.0)),
        "saved_after_draw_date": source.get("saved_after_draw_date") or ((plan94.get("saved_after_draw", {}) or {}).get("date", "")),
        "saved_after_draw_numbers": source.get("saved_after_draw_numbers") or ((plan94.get("saved_after_draw", {}) or {}).get("numbers_text", "")),
    }


def _status_snapshot(v95: dict[str, Any], v97: dict[str, Any], v98: dict[str, Any], v99: dict[str, Any]) -> dict[str, str]:
    v95_result = v95.get("result", {}) if isinstance(v95.get("result"), dict) else {}
    return {
        "step95_status": str(v95.get("status") or v95_result.get("status") or "UNKNOWN"),
        "step97_status": str(v97.get("status") or "UNKNOWN"),
        "step98_status": str(v98.get("status") or "UNKNOWN"),
        "step99_status": str(v99.get("status") or "UNKNOWN"),
    }


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _flow_snapshot() -> dict[str, Any]:
    app = _text(STREAMLIT_APP_PATH)
    add_draw = _text(ADD_DRAWS_PATH)
    save_index = add_draw.find("save_draws")
    step95_index = add_draw.find("evaluate_active_plan_against_pending_draw")
    step73_index = add_draw.find("evaluate_current_pack_against_draw")
    refresh_index = add_draw.find("refresh_models")
    return {
        "final_dashboard_page_wired": "Финално табло" in app and "render_v99_final_user_dashboard_section" in app,
        "release_lock_page_wired": "Финално заключване" in app and "render_v100_final_release_lock_section" in app,
        "add_draw_has_step95": "v95" in add_draw or "active_plan_auto_evaluation" in add_draw or "evaluate_active_plan_against_pending_draw" in add_draw,
        "add_draw_has_step97": "v97" in add_draw,
        "add_draw_has_step98": "v98" in add_draw,
        "add_draw_has_step99": "v99" in add_draw,
        "add_draw_has_step100": "v100" in add_draw,
        "save_draws_found": save_index >= 0,
        "step95_before_save": step95_index >= 0 and save_index >= 0 and step95_index < save_index,
        "step73_before_save": step73_index >= 0 and save_index >= 0 and step73_index < save_index,
        "refresh_after_save": refresh_index >= 0 and save_index >= 0 and refresh_index > save_index,
    }


def _manifest_rows() -> list[dict[str, Any]]:
    paths = [
        MODEL_PATH,
        SUMMARY_JSON_PATH,
        SUMMARY_MD_PATH,
        CHECKLIST_CSV_PATH,
        MANIFEST_CSV_PATH,
        V94_MODEL_PATH,
        V95_MODEL_PATH,
        V96_MODEL_PATH,
        V97_MODEL_PATH,
        V98_MODEL_PATH,
        V99_MODEL_PATH,
        HISTORICAL_DRAWS_PATH,
        NORMALIZED_DRAWS_PATH,
        CANONICAL_DRAWS_PATH,
        STREAMLIT_APP_PATH,
        ADD_DRAWS_PATH,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append({
            "artifact_type": "file",
            "path": path.relative_to(ROOT).as_posix() if path.is_absolute() else path.as_posix(),
            "status": "OK" if path.exists() else "MISSING",
            "note_bg": "наличен" if path.exists() else "липсва",
        })
    return rows


def _check(area_bg: str, check_bg: str, ok: bool, details_bg: str, blocking: bool = True) -> dict[str, Any]:
    return {
        "area_bg": area_bg,
        "check_bg": check_bg,
        "status": "OK" if ok else "FAIL",
        "blocking": "yes" if blocking else "no",
        "details_bg": details_bg,
    }


def build_final_release_lock() -> dict[str, Any]:
    v94 = _read_json(V94_MODEL_PATH)
    v95 = _read_json(V95_MODEL_PATH)
    v96 = _read_json(V96_MODEL_PATH)
    v97 = _read_json(V97_MODEL_PATH)
    v98 = _read_json(V98_MODEL_PATH)
    v99 = _read_json(V99_MODEL_PATH)

    dataset = _dataset_snapshot()
    active_plan = _active_plan(v94, v99)
    # step117_real_pack_alignment_v100
    played_pack = _read_json(ROOT / "reports" / "v116_played_pack_lock_report.json")
    if played_pack:
        active_plan["combination_count"] = _as_int(played_pack.get("line_count"), active_plan.get("combination_count", 0))
        active_plan["cost_eur"] = _as_float(played_pack.get("total_price_eur"), active_plan.get("cost_eur", 0.0))
        active_plan["cost_text"] = _money(active_plan.get("cost_eur", 0.0))
        active_plan["strategy_type"] = active_plan.get("strategy_type") or "Хибрид"
    statuses = _status_snapshot(v95, v97, v98, v99)
    flow = _flow_snapshot()

    checklist = [
        _check("Данни", "Dataset-ите са синхронизирани", bool(dataset.get("datasets_synced")), f"historical={dataset.get('historical_rows')}, normalized={dataset.get('normalized_rows')}, canonical={dataset.get('canonical_rows')}"),
        _check("Данни", "Последният тираж е валиден и актуален", bool(dataset.get("latest_draw_date")) and len(dataset.get("latest_numbers") or []) == 6 and int(dataset.get("historical_rows") or 0) >= 10058, f"{dataset.get('latest_draw_date')} — {dataset.get('latest_numbers_text')}"),
        _check("Активен план", "Планът е наличен", bool(active_plan.get("plan_id") or active_plan.get("strategy_type")), active_plan.get("plan_id", "")),
        _check("Активен план", "Типът е Хибрид", active_plan.get("strategy_type") == "Хибрид", active_plan.get("strategy_type", "-")),
        _check("Активен план", "Комбинациите са 12", active_plan.get("combination_count") == 12, str(active_plan.get("combination_count"))),
        _check("Активен план", "Цената е 10.80 EUR", round(_as_float(active_plan.get("cost_eur")), 2) == 10.80, active_plan.get("cost_text", "-")),
        _check("Статуси", "Step 95 е валиден за реалния цикъл", statuses.get("step95_status") in {"WAITING_NEXT_DRAW", "EVALUATED"}, statuses.get("step95_status", "UNKNOWN")),
        _check("Статуси", "Step 97 lifecycle е готов", statuses.get("step97_status") == "READY", statuses.get("step97_status", "UNKNOWN")),
        _check("Статуси", "Step 98 историята е готова", statuses.get("step98_status") in {"WAITING_NEXT_DRAW", "HAS_HISTORY"}, statuses.get("step98_status", "UNKNOWN")),
        _check("Статуси", "Step 99 финалното табло е готово", statuses.get("step99_status") == "READY_WAITING_NEXT_DRAW", statuses.get("step99_status", "UNKNOWN")),
        _check("Навигация", "Финалното табло е вързано", bool(flow.get("final_dashboard_page_wired")), "Финално табло"),
        _check("Навигация", "Финалното заключване е вързано", bool(flow.get("release_lock_page_wired")), "Финално заключване"),
        _check("Add Draw", "Step 95 pre-save проверката е преди запис", bool(flow.get("step95_before_save")), "evaluate_active_plan_against_pending_draw преди save_draws"),
        _check("Add Draw", "Step 73 pre-save проверката остава преди запис", bool(flow.get("step73_before_save")), "evaluate_current_pack_against_draw преди save_draws"),
        _check("Add Draw", "Refresh-ът е след запис", bool(flow.get("refresh_after_save")), "refresh_models след save_draws"),
        _check("Add Draw", "Step 97/98/99/100 са в refresh chain", all(bool(flow.get(key)) for key in ["add_draw_has_step97", "add_draw_has_step98", "add_draw_has_step99", "add_draw_has_step100"]), "v97, v98, v99, v100"),
    ]

    blocking_failures = [row for row in checklist if row.get("status") != "OK" and row.get("blocking") == "yes"]
    warnings = [
        "Старите raw source файлове могат да съдържат known replacement-character маркери; те не са активен UI/model/report слой.",
        "След всеки реален тираж Step 95/97/98/99/100/101 трябва да се синхронизират към новото post-draw състояние.",
    ]

    status = "V1_LOCKED_WAITING_NEXT_DRAW" if not blocking_failures else "CHECK_REQUIRED"
    payload = {
        "step": 100,
        "status": status,
        "title_bg": "Финално заключване",
        "generated_at_utc": _now_iso(),
        "active_plan": active_plan,
        "dataset": dataset,
        "statuses": statuses,
        "flow": flow,
        "checklist": checklist,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "next_action_bg": "Въведи следващия реален тираж" if status == "V1_LOCKED_WAITING_NEXT_DRAW" else "Прегледай блокиращите проверки",
        "method_bg": (
            "Step 100 заключва v1 workflow чрез контролен checklist върху Step 94–99, dataset sync, "
            "Add Draw реда и потребителската навигация. Това е QA/release слой, не прогнозен модел."
        ),
        "safe_note_bg": SAFE_NOTE_BG,
    }
    return payload


def _write_markdown(payload: dict[str, Any]) -> None:
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    statuses = payload.get("statuses", {}) or {}
    failures = payload.get("blocking_failures", []) or []
    warnings = payload.get("warnings", []) or []
    lines = [
        "# Step 100 — Финално заключване",
        "",
        f"Статус: **{payload.get('status', 'UNKNOWN')}**",
        "",
        "## Активен план",
        f"- Тип: {active_plan.get('strategy_type', '-')}",
        f"- Комбинации: {active_plan.get('combination_count', 0)}",
        f"- Цена: {active_plan.get('cost_text', '-')}",
        "",
        "## Dataset",
        f"- historical_draws.csv: {dataset.get('historical_rows', 0)} реда",
        f"- v40_normalized_draw_events.csv: {dataset.get('normalized_rows', 0)} реда",
        f"- v41_canonical_draw_events.csv: {dataset.get('canonical_rows', 0)} реда",
        f"- Последен тираж: {dataset.get('latest_draw_date', '-')} — {dataset.get('latest_numbers_text', '-')}",
        "",
        "## Статуси",
        f"- Step 95: {statuses.get('step95_status', 'UNKNOWN')}",
        f"- Step 97: {statuses.get('step97_status', 'UNKNOWN')}",
        f"- Step 98: {statuses.get('step98_status', 'UNKNOWN')}",
        f"- Step 99: {statuses.get('step99_status', 'UNKNOWN')}",
        "",
        "## Блокиращи проверки",
    ]
    if failures:
        for failure in failures:
            lines.append(f"- {failure.get('area_bg', '')}: {failure.get('check_bg', '')} — {failure.get('details_bg', '')}")
    else:
        lines.append("- Няма блокиращи проблеми.")
    lines.extend(["", "## Бележки"])
    for warning in warnings:
        lines.append(f"- {warning}")
    lines.extend(["", "## Следващо действие", payload.get("next_action_bg", "-"), "", SAFE_NOTE_BG])
    SUMMARY_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    payload = build_final_release_lock()
    _write_json(MODEL_PATH, payload)
    _write_json(SUMMARY_JSON_PATH, payload)
    _write_markdown(payload)
    _write_csv(CHECKLIST_CSV_PATH, payload.get("checklist", []) or [], CHECKLIST_FIELDS)
    _write_csv(MANIFEST_CSV_PATH, _manifest_rows(), MANIFEST_FIELDS)
    return payload


def load_final_release_lock() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        return build_and_save()
    payload = _read_json(MODEL_PATH)
    return payload if payload else build_and_save()
