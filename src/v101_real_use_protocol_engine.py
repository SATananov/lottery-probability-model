from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v101" / "v101_real_use_protocol_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v101_real_use_protocol_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v101_real_use_protocol_summary.md"
CHECKLIST_CSV_PATH = ROOT / "reports" / "v101_real_use_protocol_checklist.csv"
PROTOCOL_STEPS_CSV_PATH = ROOT / "reports" / "v101_real_use_protocol_steps.csv"

V94_MODEL_PATH = ROOT / "models" / "v94" / "v94_active_budget_plan_tracker_model.json"
V95_MODEL_PATH = ROOT / "models" / "v95" / "v95_active_plan_auto_evaluation_model.json"
V97_MODEL_PATH = ROOT / "models" / "v97" / "v97_real_draw_lifecycle_model.json"
V98_MODEL_PATH = ROOT / "models" / "v98" / "v98_active_plan_result_history_model.json"
V99_MODEL_PATH = ROOT / "models" / "v99" / "v99_final_user_dashboard_model.json"
V100_MODEL_PATH = ROOT / "models" / "v100" / "v100_final_release_lock_model.json"

HISTORICAL_DRAWS_PATH = ROOT / "data" / "historical_draws.csv"
NORMALIZED_DRAWS_PATH = ROOT / "data" / "v40_normalized_draw_events.csv"
CANONICAL_DRAWS_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
STREAMLIT_APP_PATH = ROOT / "streamlit_app.py"
ADD_DRAWS_PATH = ROOT / "src" / "add_draws_section.py"

SAFE_NOTE_BG = (
    "Step 101 е протокол за реална употреба след заключен Step 100. "
    "Той описва кога и как да се използва апът при следващ реален тираж. "
    "Не добавя нов модел, не променя математиката, не променя тегла, "
    "не генерира нови числа и не гарантира печалба."
)

CHECKLIST_FIELDS = ["area_bg", "check_bg", "status", "blocking", "details_bg"]
PROTOCOL_FIELDS = ["order", "phase_bg", "action_bg", "why_bg", "expected_result_bg"]


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


def _numbers_from_row(row: dict[str, str]) -> list[int]:
    numbers: list[int] = []
    for index in range(1, 7):
        raw = str(row.get(f"n{index}", "")).strip()
        if raw:
            try:
                numbers.append(int(raw))
            except ValueError:
                pass
    return numbers


def _dataset_info(path: Path) -> dict[str, Any]:
    rows = _read_csv_rows(path)
    info: dict[str, Any] = {
        "path": path.relative_to(ROOT).as_posix(),
        "exists": path.exists(),
        "rows": len(rows),
        "latest_draw_date": "-",
        "latest_numbers": [],
        "latest_numbers_text": "-",
        "year_min": None,
        "year_max": None,
        "rows_2026": 0,
    }
    if not rows:
        return info

    years: list[int] = []
    for row in rows:
        try:
            year = int(str(row.get("year", "")).strip())
            years.append(year)
            if year == 2026:
                info["rows_2026"] += 1
        except ValueError:
            continue
    if years:
        info["year_min"] = min(years)
        info["year_max"] = max(years)

    def sort_key(item: dict[str, str]) -> tuple[str, int, int]:
        date_value = str(item.get("date", ""))
        try:
            draw_no = int(str(item.get("draw_no", "0")).strip() or "0")
        except ValueError:
            draw_no = 0
        try:
            position = int(str(item.get("draw_position", "0")).strip() or "0")
        except ValueError:
            position = 0
        return date_value, draw_no, position

    latest = sorted(rows, key=sort_key)[-1]
    numbers = _numbers_from_row(latest)
    info["latest_draw_date"] = str(latest.get("date", "-"))
    info["latest_numbers"] = numbers
    info["latest_numbers_text"] = ", ".join(str(n) for n in numbers) if numbers else "-"
    return info


def _dataset_snapshot(v100: dict[str, Any]) -> dict[str, Any]:
    historical = _dataset_info(HISTORICAL_DRAWS_PATH)
    normalized = _dataset_info(NORMALIZED_DRAWS_PATH)
    canonical = _dataset_info(CANONICAL_DRAWS_PATH)
    rows = [historical.get("rows"), normalized.get("rows"), canonical.get("rows")]
    latest_dates = [historical.get("latest_draw_date"), normalized.get("latest_draw_date"), canonical.get("latest_draw_date")]
    latest_numbers = [historical.get("latest_numbers"), normalized.get("latest_numbers"), canonical.get("latest_numbers")]
    computed = {
        "historical": historical,
        "normalized": normalized,
        "canonical": canonical,
        "historical_rows": historical.get("rows", 0),
        "normalized_rows": normalized.get("rows", 0),
        "canonical_rows": canonical.get("rows", 0),
        "datasets_synced": len(set(rows)) == 1 and len(set(latest_dates)) == 1 and latest_numbers[0] == latest_numbers[1] == latest_numbers[2],
        "latest_draw_date": historical.get("latest_draw_date", "-"),
        "latest_numbers": historical.get("latest_numbers", []),
        "latest_numbers_text": historical.get("latest_numbers_text", "-"),
    }
    v100_dataset = v100.get("dataset") if isinstance(v100.get("dataset"), dict) else {}
    if v100_dataset and v100_dataset.get("historical_rows") == computed.get("historical_rows"):
        # Keep Step 100's already-validated summary fields, but retain the detailed computed snapshots too.
        computed.update({k: v for k, v in v100_dataset.items() if k not in {"historical", "normalized", "canonical"}})
    return computed


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _active_plan(v94: dict[str, Any], v95: dict[str, Any], v100: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for source_payload in [v100, v94]:
        active = source_payload.get("active_plan")
        if isinstance(active, dict) and active:
            candidates.append(active)
    result = v95.get("result") if isinstance(v95.get("result"), dict) else {}
    active_from_v95 = result.get("active_plan") if isinstance(result.get("active_plan"), dict) else {}
    if active_from_v95:
        candidates.append(active_from_v95)

    source = next((item for item in candidates if item.get("strategy_type") or item.get("strategy")), candidates[0] if candidates else {})
    strategy_type = source.get("strategy_type") or source.get("strategy") or source.get("plan_type") or "-"
    combination_count = int(_as_float(source.get("combination_count") or source.get("combinations_count") or source.get("selected_combinations") or 0))
    cost_eur = _as_float(source.get("cost_eur") or source.get("cost") or source.get("budget_eur"))
    return {
        "plan_id": source.get("plan_id") or source.get("id") or "active_v1_plan",
        "strategy_type": strategy_type,
        "combination_count": combination_count,
        "cost_eur": round(cost_eur, 2),
        "cost_text": f"{cost_eur:.2f} EUR" if cost_eur else str(source.get("cost_text") or "-"),
        "saved_after_draw_date": source.get("saved_after_draw_date") or (source.get("saved_after_draw") or {}).get("date") if isinstance(source.get("saved_after_draw"), dict) else source.get("saved_after_draw_date"),
        "saved_after_draw_numbers": source.get("saved_after_draw_numbers") or (source.get("saved_after_draw") or {}).get("numbers_text") if isinstance(source.get("saved_after_draw"), dict) else source.get("saved_after_draw_numbers"),
    }


def _flow_snapshot() -> dict[str, Any]:
    app_text = STREAMLIT_APP_PATH.read_text(encoding="utf-8") if STREAMLIT_APP_PATH.exists() else ""
    add_text = ADD_DRAWS_PATH.read_text(encoding="utf-8") if ADD_DRAWS_PATH.exists() else ""
    save_pos = add_text.find("save_draws(")
    refresh_candidates = [
        add_text.find("model_results = refresh_models("),
        add_text.find("refresh_models("),
        add_text.find("refresh_models()"),
    ]
    refresh_pos = next((idx for idx in refresh_candidates if idx != -1), -1)
    step73_pos = add_text.find("evaluate_current_pack_against_draw")
    step95_pos = add_text.find("evaluate_active_plan_against_pending_draw")
    step100_script_pos = add_text.find("v100_build_final_release_lock.py")
    step101_script_pos = add_text.find("v101_build_real_use_protocol.py")
    return {
        "real_use_protocol_page_wired": "Протокол за реална употреба" in app_text and "render_v101_real_use_protocol_page" in app_text,
        "step73_before_save": step73_pos != -1 and save_pos != -1 and step73_pos < save_pos,
        "step95_before_save": step95_pos != -1 and save_pos != -1 and step95_pos < save_pos,
        "refresh_after_save": refresh_pos != -1 and save_pos != -1 and refresh_pos > save_pos,
        "add_draw_has_step100": step100_script_pos != -1,
        "add_draw_has_step101": step101_script_pos != -1,
        "step101_after_step100": step100_script_pos != -1 and step101_script_pos != -1 and step101_script_pos > step100_script_pos,
    }


def _status_snapshot(v95: dict[str, Any], v97: dict[str, Any], v98: dict[str, Any], v99: dict[str, Any], v100: dict[str, Any]) -> dict[str, str]:
    v95_result = v95.get("result", {}) if isinstance(v95.get("result"), dict) else {}
    return {
        "step95_status": str(v95.get("status") or v95_result.get("status") or "UNKNOWN"),
        "step97_status": str(v97.get("status") or "UNKNOWN"),
        "step98_status": str(v98.get("status") or "UNKNOWN"),
        "step99_status": str(v99.get("status") or "UNKNOWN"),
        "step100_status": str(v100.get("status") or "UNKNOWN"),
    }


def _check(area: str, label: str, ok: bool, details: str, blocking: bool = True) -> dict[str, str]:
    return {
        "area_bg": area,
        "check_bg": label,
        "status": "OK" if ok else "FAIL",
        "blocking": "yes" if blocking else "no",
        "details_bg": details,
    }


def _protocol_steps() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "phase_bg": "Преди следващия тираж",
            "action_bg": "Запази Step 100 като заключен V1 checkpoint и не променяй модели, тегла или генератори преди реалната проверка.",
            "why_bg": "Така първият реален цикъл ще измери заключената система, а не нова смесена версия.",
            "expected_result_bg": "Проектът остава във V1_LOCKED_WAITING_NEXT_DRAW.",
        },
        {
            "order": 2,
            "phase_bg": "Когато излезе новият тираж",
            "action_bg": "Отвори Добавяне на тираж и въведи реалните числа точно както са публикувани.",
            "why_bg": "Ръчният вход трябва да е ясен и проверим, преди dataset-ът да се промени.",
            "expected_result_bg": "Pending draw е готов за pre-save оценка.",
        },
        {
            "order": 3,
            "phase_bg": "Преди запис",
            "action_bg": "Остави включени pre-save оценките на Step 73 и Step 95.",
            "why_bg": "Те сравняват активния пакет/план срещу новия тираж преди dataset update.",
            "expected_result_bg": "Има оценка на активния план преди запис.",
        },
        {
            "order": 4,
            "phase_bg": "Запис и обновяване",
            "action_bg": "Запиши тиража и пусни refresh chain-а след save.",
            "why_bg": "След записа се обновяват history, result tracking, final dashboard, release lock и този протокол.",
            "expected_result_bg": "Step 96–101 са обновени след реалния draw.",
        },
        {
            "order": 5,
            "phase_bg": "След обновяване",
            "action_bg": "Прегледай История на активния план, Финално табло, Финално заключване и Протокол за реална употреба.",
            "why_bg": "Това е реалният operational review, не нова прогноза.",
            "expected_result_bg": "Ясно се вижда как се е представил активният план.",
        },
        {
            "order": 6,
            "phase_bg": "След проверка",
            "action_bg": "Комитни само ако compile/JSON/CSV/Cyrillic/checkpoint проверките са чисти, после направи clean ZIP.",
            "why_bg": "Така следващият checkpoint остава проверим и възстановим.",
            "expected_result_bg": "Нов clean checkpoint след първи реален цикъл.",
        },
    ]


def build_real_use_protocol() -> dict[str, Any]:
    v94 = _read_json(V94_MODEL_PATH)
    v95 = _read_json(V95_MODEL_PATH)
    v97 = _read_json(V97_MODEL_PATH)
    v98 = _read_json(V98_MODEL_PATH)
    v99 = _read_json(V99_MODEL_PATH)
    v100 = _read_json(V100_MODEL_PATH)

    dataset = _dataset_snapshot(v100)
    active_plan = _active_plan(v94, v95, v100)
    # step117_real_pack_alignment_v101
    played_pack = _read_json(ROOT / "reports" / "v116_played_pack_lock_report.json")
    if played_pack:
        active_plan["combination_count"] = int(_as_float(played_pack.get("line_count") or active_plan.get("combination_count") or 0))
        active_plan["cost_eur"] = round(_as_float(played_pack.get("total_price_eur") or active_plan.get("cost_eur") or 0), 2)
        active_plan["cost_text"] = f"{active_plan.get('cost_eur', 0.0):.2f} EUR"
        active_plan["strategy_type"] = active_plan.get("strategy_type") or "Хибрид"
    statuses = _status_snapshot(v95, v97, v98, v99, v100)
    flow = _flow_snapshot()
    protocol_steps = _protocol_steps()

    step100_failures = v100.get("blocking_failures", []) if isinstance(v100.get("blocking_failures"), list) else []

    checklist = [
        _check("Step 100", "V1 lock е активен", statuses.get("step100_status") == "V1_LOCKED_WAITING_NEXT_DRAW", statuses.get("step100_status", "UNKNOWN")),
        _check("Step 100", "Няма Step 100 blocking failures", len(step100_failures) == 0, f"blocking_failures={len(step100_failures)}"),
        _check("Данни", "Dataset-ите са синхронизирани", bool(dataset.get("datasets_synced")), f"historical={dataset.get('historical_rows')}, normalized={dataset.get('normalized_rows')}, canonical={dataset.get('canonical_rows')}"),
        _check("Данни", "Последният тираж е валиден и актуален", bool(dataset.get("latest_draw_date")) and len(dataset.get("latest_numbers") or []) == 6 and int(dataset.get("historical_rows") or 0) >= 10058, f"{dataset.get('latest_draw_date')} — {dataset.get('latest_numbers_text')}"),
        _check("Активен план", "Активният план е Хибрид", active_plan.get("strategy_type") == "Хибрид", active_plan.get("strategy_type", "-")),
        _check("Активен план", "Планът има 12 комбинации", active_plan.get("combination_count") == 12, str(active_plan.get("combination_count"))),
        _check("Активен план", "Бюджетът е 10.80 EUR", round(_as_float(active_plan.get("cost_eur")), 2) == 10.80, active_plan.get("cost_text", "-")),
        _check("Add Draw", "Step 73 pre-save остава преди save", bool(flow.get("step73_before_save")), "evaluate_current_pack_against_draw преди save_draws"),
        _check("Add Draw", "Step 95 pre-save остава преди save", bool(flow.get("step95_before_save")), "evaluate_active_plan_against_pending_draw преди save_draws"),
        _check("Add Draw", "Refresh chain остава след save", bool(flow.get("refresh_after_save")), "refresh_models след save_draws"),
        _check("Add Draw", "Step 101 е след Step 100 в refresh chain", bool(flow.get("step101_after_step100")), "v101_build_real_use_protocol.py след v100_build_final_release_lock.py"),
        _check("Навигация", "Страницата е вързана в app-а", bool(flow.get("real_use_protocol_page_wired")), "Протокол за реална употреба"),
    ]

    blocking_failures = [row for row in checklist if row.get("status") != "OK" and row.get("blocking") == "yes"]
    status = "WAITING_NEXT_REAL_DRAW" if not blocking_failures else "CHECK_REQUIRED"

    return {
        "step": 101,
        "status": status,
        "title_bg": "Протокол за реална употреба",
        "generated_at_utc": _now_iso(),
        "step100_status": statuses.get("step100_status", "UNKNOWN"),
        "active_plan": active_plan,
        "dataset": dataset,
        "statuses": statuses,
        "flow": flow,
        "protocol_steps": protocol_steps,
        "checklist": checklist,
        "blocking_failures": blocking_failures,
        "next_action_bg": "Изчакай следващия реален тираж и го въведи през Добавяне на тираж." if status == "WAITING_NEXT_REAL_DRAW" else "Прегледай блокиращите проверки преди реална употреба.",
        "method_bg": "Step 101 е operational protocol слой. Той фиксира реда на работа след Step 100 и не променя прогнозната логика.",
        "safe_note_bg": SAFE_NOTE_BG,
        "locked_scope_bg": "Без нови модели, без промяна на тегла, без промяна на ticket builder, без промяна на dataset преди следващ реален тираж.",
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    failures = payload.get("blocking_failures", []) or []
    lines = [
        "# Step 101 — Протокол за реална употреба",
        "",
        f"Статус: **{payload.get('status', 'UNKNOWN')}**",
        f"Step 100: **{payload.get('step100_status', 'UNKNOWN')}**",
        "",
        "## Активен план",
        f"- Тип: {active_plan.get('strategy_type', '-')}",
        f"- Комбинации: {active_plan.get('combination_count', 0)}",
        f"- Цена: {active_plan.get('cost_text', '-')}",
        "",
        "## Dataset checkpoint",
        f"- Редове: {dataset.get('historical_rows', 0)}",
        f"- Последен тираж: {dataset.get('latest_draw_date', '-')} — {dataset.get('latest_numbers_text', '-')}",
        "",
        "## Протокол",
    ]
    for step in payload.get("protocol_steps", []) or []:
        lines.append(f"{step.get('order')}. **{step.get('phase_bg')}** — {step.get('action_bg')}")
    lines.extend(["", "## Блокиращи проверки"])
    if failures:
        for failure in failures:
            lines.append(f"- {failure.get('area_bg', '')}: {failure.get('check_bg', '')} — {failure.get('details_bg', '')}")
    else:
        lines.append("- Няма блокиращи проблеми.")
    lines.extend([
        "",
        "## Следващо действие",
        payload.get("next_action_bg", "-"),
        "",
        payload.get("locked_scope_bg", ""),
        "",
        SAFE_NOTE_BG,
    ])
    SUMMARY_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    payload = build_real_use_protocol()
    _write_json(MODEL_PATH, payload)
    _write_json(SUMMARY_JSON_PATH, payload)
    _write_markdown(payload)
    _write_csv(CHECKLIST_CSV_PATH, payload.get("checklist", []) or [], CHECKLIST_FIELDS)
    _write_csv(PROTOCOL_STEPS_CSV_PATH, payload.get("protocol_steps", []) or [], PROTOCOL_FIELDS)
    return payload


def load_real_use_protocol() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        return build_and_save()
    payload = _read_json(MODEL_PATH)
    return payload if payload else build_and_save()
