from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v99" / "v99_final_user_dashboard_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v99_final_user_dashboard_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v99_final_user_dashboard_summary.md"
ACTIONS_CSV_PATH = ROOT / "reports" / "v99_final_user_dashboard_actions.csv"
SNAPSHOT_CSV_PATH = ROOT / "reports" / "v99_final_user_dashboard_snapshot.csv"

V94_MODEL_PATH = ROOT / "models" / "v94" / "v94_active_budget_plan_tracker_model.json"
V95_MODEL_PATH = ROOT / "models" / "v95" / "v95_active_plan_auto_evaluation_model.json"
V96_MODEL_PATH = ROOT / "models" / "v96" / "v96_add_draw_controlled_flow_model.json"
V97_MODEL_PATH = ROOT / "models" / "v97" / "v97_real_draw_lifecycle_model.json"
V98_MODEL_PATH = ROOT / "models" / "v98" / "v98_active_plan_result_history_model.json"
HISTORICAL_DRAWS_PATH = ROOT / "data" / "historical_draws.csv"
CANONICAL_DRAWS_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"

SAFE_NOTE_BG = (
    "Step 99 е финално потребителско табло. То обединява вече създадените проверки, "
    "активния план, историята и следващото действие. Не добавя нова прогноза, "
    "не променя математиката и не гарантира печалба."
)

ACTION_FIELDS = [
    "order",
    "status",
    "title_bg",
    "description_bg",
    "page_bg",
    "is_ready",
]

SNAPSHOT_FIELDS = [
    "metric",
    "value",
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


def _numbers_text(numbers: Any) -> str:
    if isinstance(numbers, str):
        return numbers
    if isinstance(numbers, list):
        cleaned: list[int] = []
        for item in numbers:
            number = _as_int(item, -1)
            if 1 <= number <= 49:
                cleaned.append(number)
        if cleaned:
            return ", ".join(str(n) for n in cleaned)
    return ""


def _load_dataset_snapshot() -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    if HISTORICAL_DRAWS_PATH.exists():
        with HISTORICAL_DRAWS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            rows = [dict(row) for row in csv.DictReader(f)]

    latest = rows[-1] if rows else {}
    latest_numbers = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        number = _as_int(latest.get(key), 0)
        if number:
            latest_numbers.append(number)

    canonical_rows = 0
    if CANONICAL_DRAWS_PATH.exists():
        with CANONICAL_DRAWS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            canonical_rows = sum(1 for _ in csv.DictReader(f))

    return {
        "dataset_rows": len(rows),
        "canonical_rows": canonical_rows,
        "latest_draw_date": latest.get("date", ""),
        "latest_draw_year": latest.get("year", ""),
        "latest_draw_number": latest.get("draw_no") or latest.get("draw_number") or "",
        "latest_draw_position": latest.get("draw_position", ""),
        "latest_numbers": latest_numbers,
        "latest_numbers_text": _numbers_text(latest_numbers),
    }


def _active_plan_from_sources(
    v94: dict[str, Any],
    v96: dict[str, Any],
    v97: dict[str, Any],
    v98: dict[str, Any],
) -> dict[str, Any]:
    plan94 = v94.get("active_plan", {}) if isinstance(v94.get("active_plan"), dict) else {}
    plan98 = v98.get("active_plan", {}) if isinstance(v98.get("active_plan"), dict) else {}

    v96_snapshot = v96.get("current_snapshot", {}) if isinstance(v96.get("current_snapshot"), dict) else {}
    v97_state = v97.get("current_state", {}) if isinstance(v97.get("current_state"), dict) else {}
    plan97 = v97_state.get("active_plan", {}) if isinstance(v97_state.get("active_plan"), dict) else {}

    if plan97.get("plan_source") == "v117_real_ticket_pack_builder" or v96_snapshot.get("active_plan_snapshot_source") == "v117_real_ticket_pack_builder":
        source = plan97 or {}
        count = _as_int(source.get("combination_count") or v96_snapshot.get("active_plan_combinations"), 0)
        cost = _as_float(source.get("cost_eur") or v96_snapshot.get("active_plan_cost_eur"), 0.0)
        return {
            "plan_id": source.get("plan_id") or plan94.get("plan_id", ""),
            "status": "ACTIVE",
            "strategy_type": source.get("strategy_type") or v96_snapshot.get("active_plan_type") or plan94.get("strategy_type", ""),
            "strategy_label": "Готов фиш пакет · 3 фиша × 4 комбинации",
            "combination_count": count,
            "cost_eur": round(cost, 2),
            "cost_text": f"{cost:.2f}",
            "saved_after_draw_date": source.get("saved_after_draw_date") or ((plan94.get("saved_after_draw", {}) or {}).get("date", "")),
            "saved_after_draw_numbers": source.get("saved_after_draw_numbers") or ((plan94.get("saved_after_draw", {}) or {}).get("numbers_text", "")),
            "real_result_rows": _as_int(plan98.get("real_result_rows"), 0),
            "next_status_bg": plan98.get("next_status_bg", ""),
            "plan_source": "v117_real_ticket_pack_builder",
            "ticket_count": _as_int(source.get("ticket_count"), 3),
            "lines_per_ticket": _as_int(source.get("lines_per_ticket"), 4),
            "combinations": plan94.get("combinations", []) or [],
        }

    source = plan98 or plan94
    return {
        "plan_id": source.get("plan_id", ""),
        "status": source.get("status", "ACTIVE" if source else "MISSING"),
        "strategy_type": source.get("strategy_type", ""),
        "strategy_label": source.get("strategy_label", plan94.get("strategy_label", "")),
        "combination_count": _as_int(source.get("combination_count"), 0),
        "cost_eur": _as_float(source.get("cost_eur"), 0.0),
        "cost_text": source.get("cost_text") or f"{_as_float(source.get('cost_eur'), 0.0):.2f}",
        "saved_after_draw_date": source.get("saved_after_draw_date") or ((plan94.get("saved_after_draw", {}) or {}).get("date", "")),
        "saved_after_draw_numbers": source.get("saved_after_draw_numbers") or ((plan94.get("saved_after_draw", {}) or {}).get("numbers_text", "")),
        "real_result_rows": _as_int(source.get("real_result_rows"), 0),
        "next_status_bg": source.get("next_status_bg", ""),
        "plan_source": "v98_or_v94",
        "combinations": plan94.get("combinations", []) or [],
    }


def _statuses(v95: dict[str, Any], v96: dict[str, Any], v97: dict[str, Any], v98: dict[str, Any]) -> dict[str, str]:
    v95_result = v95.get("result", {}) if isinstance(v95.get("result"), dict) else {}
    v96_snapshot = v96.get("current_snapshot", {}) if isinstance(v96.get("current_snapshot"), dict) else {}
    return {
        "step95_status": str(v95.get("status") or v95_result.get("status") or "UNKNOWN"),
        "step96_status": str(v96.get("status") or "UNKNOWN"),
        "step97_status": str(v97.get("status") or "UNKNOWN"),
        "step98_status": str(v98.get("status") or "UNKNOWN"),
        "active_plan_available": str(bool(v96_snapshot.get("active_plan_available"))).lower(),
    }


def _next_action(active_plan: dict[str, Any], statuses: dict[str, str]) -> dict[str, Any]:
    has_plan = bool(active_plan.get("plan_id")) and active_plan.get("strategy_type")
    if not has_plan:
        return {
            "title_bg": "Създай активен бюджетен план",
            "description_bg": "Отвори Бюджетен съветник, избери бюджет и запази активен план преди следващия тираж.",
            "page_bg": "Бюджетен съветник",
            "priority": "HIGH",
        }

    if statuses.get("step95_status") == "WAITING_NEXT_DRAW":
        return {
            "title_bg": "Въведи следващия реален тираж",
            "description_bg": "Когато излезе новият тираж, отвори Добавяне на тираж. Step 95 ще оцени активния план преди запис, Step 97/98 ще обновят lifecycle и историята.",
            "page_bg": "Добавяне на тираж",
            "priority": "HIGH",
        }

    if statuses.get("step98_status") == "WAITING_NEXT_DRAW":
        return {
            "title_bg": "Провери историята след следващ резултат",
            "description_bg": "Историята ще се попълни автоматично след реален нов тираж след активния план.",
            "page_bg": "История на активния план",
            "priority": "MEDIUM",
        }

    return {
        "title_bg": "Прегледай резултата и реши дали да обновиш плана",
        "description_bg": "След реален резултат прегледай История на активния план, после използвай Бюджетен съветник при нужда от нов план.",
        "page_bg": "История на активния план",
        "priority": "MEDIUM",
    }


def _build_actions(active_plan: dict[str, Any], statuses: dict[str, str]) -> list[dict[str, Any]]:
    has_plan = bool(active_plan.get("plan_id"))
    waiting = statuses.get("step95_status") == "WAITING_NEXT_DRAW"
    return [
        {
            "order": 1,
            "status": "готово" if has_plan else "липсва",
            "title_bg": "Активен план",
            "description_bg": "Планът е избран и заключен за следващия реален тираж." if has_plan else "Първо запази активен план от Бюджетен съветник.",
            "page_bg": "План и резултат",
            "is_ready": has_plan,
        },
        {
            "order": 2,
            "status": "чака" if waiting else "проверено",
            "title_bg": "Следващ реален тираж",
            "description_bg": "Въведи новия тираж в Добавяне на тираж. Pre-save проверките трябва да останат включени.",
            "page_bg": "Добавяне на тираж",
            "is_ready": has_plan,
        },
        {
            "order": 3,
            "status": statuses.get("step97_status", "UNKNOWN"),
            "title_bg": "Lifecycle контрол",
            "description_bg": "Провери реда на процеса: оценка преди запис, запис, refresh, история и sync.",
            "page_bg": "Реален цикъл на тираж",
            "is_ready": statuses.get("step97_status") == "READY",
        },
        {
            "order": 4,
            "status": statuses.get("step98_status", "UNKNOWN"),
            "title_bg": "История на резултатите",
            "description_bg": "След нов реален тираж тук ще се вижда колко попадения е дал активният план.",
            "page_bg": "История на активния план",
            "is_ready": True,
        },
    ]


def _snapshot_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    statuses = payload.get("statuses", {}) or {}
    next_action = payload.get("next_action", {}) or {}
    return [
        {"metric": "Активен план", "value": active_plan.get("strategy_type", "-"), "note_bg": active_plan.get("plan_id", "")},
        {"metric": "Комбинации", "value": active_plan.get("combination_count", 0), "note_bg": "Брой редове в активния план"},
        {"metric": "Цена", "value": _money(active_plan.get("cost_eur", 0.0)), "note_bg": "Очаквана цена на активния план"},
        {"metric": "Step 95", "value": statuses.get("step95_status", "UNKNOWN"), "note_bg": "Статус на pre-save оценката"},
        {"metric": "Step 97", "value": statuses.get("step97_status", "UNKNOWN"), "note_bg": "Статус на lifecycle контрола"},
        {"metric": "Step 98", "value": statuses.get("step98_status", "UNKNOWN"), "note_bg": "Статус на историята"},
        {"metric": "Dataset редове", "value": dataset.get("dataset_rows", 0), "note_bg": dataset.get("latest_numbers_text", "")},
        {"metric": "Следващо действие", "value": next_action.get("title_bg", "-"), "note_bg": next_action.get("page_bg", "")},
    ]


def build_final_user_dashboard() -> dict[str, Any]:
    v94 = _read_json(V94_MODEL_PATH)
    v95 = _read_json(V95_MODEL_PATH)
    v96 = _read_json(V96_MODEL_PATH)
    v97 = _read_json(V97_MODEL_PATH)
    v98 = _read_json(V98_MODEL_PATH)

    active_plan = _active_plan_from_sources(v94, v96, v97, v98)
    dataset = _load_dataset_snapshot()
    statuses = _statuses(v95, v96, v97, v98)
    next_action = _next_action(active_plan, statuses)
    actions = _build_actions(active_plan, statuses)

    issues: list[str] = []
    warnings: list[str] = []
    if not active_plan.get("plan_id"):
        issues.append("Няма активен план.")

    step95_status = statuses.get("step95_status")
    step97_status = statuses.get("step97_status")
    step98_status = statuses.get("step98_status")
    dataset_rows = int(dataset.get("dataset_rows") or 0)
    canonical_rows = int(dataset.get("canonical_rows") or 0)

    if step95_status not in {"WAITING_NEXT_DRAW", "EVALUATED", "DRAW_NOT_AFTER_ACTIVE_PLAN", "NO_ACTIVE_PLAN"}:
        issues.append(f"Step 95 статусът е неочакван: {step95_status}")
    if step97_status not in {"READY", "POST_DRAW_RECORDED"}:
        issues.append(f"Step 97 lifecycle не е готов за следващ цикъл: {step97_status}")
    if step98_status not in {"WAITING_NEXT_DRAW", "HAS_HISTORY"}:
        issues.append(f"Step 98 историята е в неочакван статус: {step98_status}")
    if dataset_rows < 10058:
        issues.append(f"Dataset-ът има по-малко редове от базовия checkpoint: {dataset_rows}")
    if canonical_rows and canonical_rows != dataset_rows:
        issues.append(f"Canonical dataset не е синхронизиран: canonical={canonical_rows}, historical={dataset_rows}")
    if dataset_rows > 10058:
        warnings.append("Има реален тираж след заключената контролна точка; това е нормално състояние след тираж.")

    dashboard_status = "READY_WAITING_NEXT_DRAW" if not issues else "CHECK_REQUIRED"

    payload = {
        "step": 99,
        "status": dashboard_status,
        "title_bg": "Финално потребителско табло",
        "generated_at_utc": _now_iso(),
        "active_plan": active_plan,
        "dataset": dataset,
        "statuses": statuses,
        "next_action": next_action,
        "actions": actions,
        "issues": issues,
        "warnings": warnings,
        "source_files": {
            "active_plan": "models/v97/v97_real_draw_lifecycle_model.json + models/v96/v96_add_draw_controlled_flow_model.json",
            "step95": "models/v95/v95_active_plan_auto_evaluation_model.json",
            "step96": "models/v96/v96_add_draw_controlled_flow_model.json",
            "step97": "models/v97/v97_real_draw_lifecycle_model.json",
            "step98": "models/v98/v98_active_plan_result_history_model.json",
        },
        "method_bg": (
            "Step 99 събира най-важното от Step 94 до Step 98 в един потребителски екран: "
            "активен план, текущ статус, последен dataset, следващо действие, lifecycle и история."
        ),
        "safe_note_bg": SAFE_NOTE_BG,
    }
    return payload


def _write_markdown(payload: dict[str, Any]) -> None:
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    statuses = payload.get("statuses", {}) or {}
    next_action = payload.get("next_action", {}) or {}
    lines = [
        "# Step 99 — Финално потребителско табло",
        "",
        f"Статус: **{payload.get('status', 'UNKNOWN')}**",
        "",
        "## Активен план",
        f"- Тип: {active_plan.get('strategy_type', '-')}",
        f"- Комбинации: {active_plan.get('combination_count', 0)}",
        f"- Цена: {_money(active_plan.get('cost_eur', 0.0))}",
        f"- Заключен след: {active_plan.get('saved_after_draw_date', '-')} — {active_plan.get('saved_after_draw_numbers', '-')}",
        "",
        "## Статуси",
        f"- Step 95: {statuses.get('step95_status', 'UNKNOWN')}",
        f"- Step 97: {statuses.get('step97_status', 'UNKNOWN')}",
        f"- Step 98: {statuses.get('step98_status', 'UNKNOWN')}",
        "",
        "## Dataset",
        f"- Редове: {dataset.get('dataset_rows', 0)}",
        f"- Последен тираж: {dataset.get('latest_draw_date', '-')} — {dataset.get('latest_numbers_text', '-')}",
        "",
        "## Следващо действие",
        f"- {next_action.get('title_bg', '-')}",
        f"- {next_action.get('description_bg', '-')}",
        "",
        f"> {SAFE_NOTE_BG}",
        "",
    ]
    SUMMARY_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    payload = build_final_user_dashboard()
    _write_json(MODEL_PATH, payload)
    _write_json(SUMMARY_JSON_PATH, payload)
    _write_markdown(payload)
    _write_csv(ACTIONS_CSV_PATH, payload.get("actions", []) or [], ACTION_FIELDS)
    _write_csv(SNAPSHOT_CSV_PATH, _snapshot_rows(payload), SNAPSHOT_FIELDS)
    return payload


def load_final_user_dashboard() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        return build_and_save()
    payload = _read_json(MODEL_PATH)
    return payload or build_and_save()
