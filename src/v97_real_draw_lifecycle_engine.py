from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"
V97_DIR = MODELS_DIR / "v97"

MODEL_JSON = V97_DIR / "v97_real_draw_lifecycle_model.json"
SUMMARY_JSON = REPORTS_DIR / "v97_real_draw_lifecycle_summary.json"
SUMMARY_MD = REPORTS_DIR / "v97_real_draw_lifecycle_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v97_real_draw_lifecycle_checklist.csv"
ARTIFACTS_CSV = REPORTS_DIR / "v97_real_draw_lifecycle_artifacts.csv"

V94_MODEL = MODELS_DIR / "v94" / "v94_active_budget_plan_tracker_model.json"
V95_MODEL = MODELS_DIR / "v95" / "v95_active_plan_auto_evaluation_model.json"
V96_MODEL = MODELS_DIR / "v96" / "v96_add_draw_controlled_flow_model.json"
V117_SUMMARY = REPORTS_DIR / "v117_real_ticket_pack_builder_summary.json"
V95_HISTORY = REPORTS_DIR / "v95_active_plan_auto_evaluation_history.csv"
ADD_DRAWS_SECTION = ROOT / "src" / "add_draws_section.py"
V95_ENGINE = ROOT / "src" / "v95_active_plan_auto_evaluation_engine.py"
DATASET_PATHS = [
    DATA_DIR / "historical_draws.csv",
    DATA_DIR / "v40_normalized_draw_events.csv",
    DATA_DIR / "v41_canonical_draw_events.csv",
]

SAFE_NOTE_BG = (
    "Step 97 е контролен слой за реалния цикъл на нов тираж: преди запис, запис, обновяване, "
    "проверка и clean checkpoint. Той не променя прогнозната математика и не обещава печалба."
)

LIFECYCLE_ROWS: list[dict[str, Any]] = [
    {
        "step_order": 1,
        "phase_bg": "Подготовка",
        "page_bg": "План и резултат / Бюджетен съветник",
        "action_bg": "Потребителят има запазен активен бюджетен план преди следващия реален тираж.",
        "expected_artifact_bg": "models/v94/v94_active_budget_plan_tracker_model.json",
        "guard_bg": "Планът помни последния тираж, след който е запазен, за да няма backfit.",
        "status_rule_bg": "Активният план трябва да е наличен и да има комбинации.",
    },
    {
        "step_order": 2,
        "phase_bg": "Pre-save проверка",
        "page_bg": "Добавяне на тираж",
        "action_bg": "Step 95 оценява активния план със същите въведени числа преди запис в dataset-а.",
        "expected_artifact_bg": "reports/v95_active_plan_auto_evaluation_latest_result.csv",
        "guard_bg": "Ако тиражът не е след активния план, Step 95 не записва реален резултат.",
        "status_rule_bg": "Статусът е EVALUATED само за реално следващ тираж; иначе остава WAITING/DRAW_NOT_AFTER_ACTIVE_PLAN.",
    },
    {
        "step_order": 3,
        "phase_bg": "Pre-save пакет",
        "page_bg": "Добавяне на тираж",
        "action_bg": "Step 73 оценява текущия пакет преди dataset refresh.",
        "expected_artifact_bg": "reports/v73_ticket_pack_performance_history.csv",
        "guard_bg": "Оценката се прави преди новите числа да станат част от историческите данни.",
        "status_rule_bg": "При грешка записът се спира.",
    },
    {
        "step_order": 4,
        "phase_bg": "Запис",
        "page_bg": "Добавяне на тираж",
        "action_bg": "След успешни проверки новият тираж се записва в historical_draws.csv.",
        "expected_artifact_bg": "data/historical_draws.csv",
        "guard_bg": "Валидни 6 различни числа между 1 и 49; bonus не се смесва с основните числа.",
        "status_rule_bg": "Dataset row count се увеличава само след успешен запис или replace на съществуващо теглене.",
    },
    {
        "step_order": 5,
        "phase_bg": "Обновяване",
        "page_bg": "Добавяне на тираж / Обновяване на анализите",
        "action_bg": "След запис се изпълнява refresh chain за зависимите модели и отчети.",
        "expected_artifact_bg": "models/ и reports/",
        "guard_bg": "Step 94/95/96/97 са в края на веригата, за да отчетат актуалното състояние.",
        "status_rule_bg": "Всички важни build scripts трябва да минават без грешка.",
    },
    {
        "step_order": 6,
        "phase_bg": "Синхрон",
        "page_bg": "GitHub sync / Контрол на синхрона",
        "action_bg": "След refresh промените се commit/push-ват и Git статусът се изчиства.",
        "expected_artifact_bg": "Git commit + чист working tree",
        "guard_bg": "Не се прави clean ZIP при нечист статус.",
        "status_rule_bg": "git status --short трябва да е празен.",
    },
    {
        "step_order": 7,
        "phase_bg": "Checkpoint",
        "page_bg": "Финален пакет / clean ZIP",
        "action_bg": "Създава се clean ZIP от committed Git state и се проверява строго.",
        "expected_artifact_bg": "*_FINAL-clean_*.zip",
        "guard_bg": "Без helper/cache/temp/patch/nested ZIP файлове и без broken Cyrillic.",
        "status_rule_bg": "ZIP integrity, compile, JSON/CSV parse и логическите проверки трябва да минат.",
    },
]

ARTIFACT_ROWS: list[dict[str, Any]] = [
    {"artifact_group": "Активен план", "path": "models/v94/v94_active_budget_plan_tracker_model.json", "purpose_bg": "Пази заключения бюджетен план и комбинациите за следващ тираж.", "owner_step": "94"},
    {"artifact_group": "Pre-save резултат", "path": "models/v95/v95_active_plan_auto_evaluation_model.json", "purpose_bg": "Пази последния статус на автоматичната проверка на активния план.", "owner_step": "95"},
    {"artifact_group": "Pre-save history", "path": "reports/v95_active_plan_auto_evaluation_history.csv", "purpose_bg": "Пази реална история само когато има нов тираж след активния план.", "owner_step": "95"},
    {"artifact_group": "Контролиран ред", "path": "models/v96/v96_add_draw_controlled_flow_model.json", "purpose_bg": "Показва правилния ред в страницата Добавяне на тираж.", "owner_step": "96"},
    {"artifact_group": "Реален цикъл", "path": "models/v97/v97_real_draw_lifecycle_model.json", "purpose_bg": "Обобщава lifecycle състоянието и readiness за следващ реален тираж.", "owner_step": "97"},
    {"artifact_group": "Основен dataset", "path": "data/historical_draws.csv", "purpose_bg": "Реалният исторически dataset, който се обновява след Add Draw.", "owner_step": "core"},
    {"artifact_group": "Canonical dataset", "path": "data/v41_canonical_draw_events.csv", "purpose_bg": "Каноничният набор от събития за моделните build стъпки.", "owner_step": "41"},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


def _dataset_stats(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    result: dict[str, Any] = {
        "path": path.relative_to(ROOT).as_posix(),
        "exists": path.exists(),
        "rows": len(rows),
        "latest_date": "",
        "latest_numbers": "",
        "latest_year": "",
        "parse_ok": path.exists(),
    }
    if not rows:
        return result
    latest = rows[-1]
    numbers = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = str(latest.get(key, "")).strip()
        if value:
            try:
                numbers.append(str(int(float(value))))
            except Exception:
                numbers.append(value)
    result["latest_date"] = str(latest.get("date") or latest.get("draw_date") or "")[:10]
    result["latest_year"] = str(latest.get("year", ""))
    result["latest_draw_no"] = str(latest.get("draw_no") or latest.get("draw_number") or "")
    result["latest_position"] = str(latest.get("draw_position") or latest.get("drawing_no") or "")
    result["latest_numbers"] = ",".join(numbers)
    return result


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


def _real_ticket_pack_snapshot() -> dict[str, Any]:
    payload = _read_json(V117_SUMMARY)
    if not payload:
        return {}
    total_lines = _as_int(payload.get("total_lines"), 0)
    total_price = _as_float(payload.get("total_price_eur"), 0.0)
    if total_lines <= 0 or total_price <= 0:
        return {}
    return {
        "active_plan_available": True,
        "plan_id": payload.get("plan_id", ""),
        "strategy_type": payload.get("strategy_type", ""),
        "combination_count": total_lines,
        "cost_eur": total_price,
        "cost_text": f"{total_price:.2f}",
        "ticket_count": _as_int(payload.get("ticket_count"), 0),
        "lines_per_ticket": _as_int(payload.get("lines_per_ticket"), 0),
        "plan_source": "v117_real_ticket_pack_builder",
        "plan_label_bg": "готов фиш пакет",
    }


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except Exception:
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip().replace(",", "."))
    except Exception:
        return default


def _active_plan_snapshot() -> dict[str, Any]:
    real_pack = _real_ticket_pack_snapshot()
    if real_pack:
        return real_pack

    v94 = _read_json(V94_MODEL)
    plan = _find_active_plan(v94)
    combinations = plan.get("combinations", []) if isinstance(plan.get("combinations", []), list) else []
    return {
        "active_plan_available": bool(plan),
        "plan_id": plan.get("plan_id", ""),
        "strategy_type": plan.get("strategy_type") or plan.get("recommended_type") or "",
        "combination_count": _as_int(plan.get("combination_count") or len(combinations), 0),
        "cost_eur": _as_float(plan.get("cost_eur") or plan.get("estimated_cost_eur"), 0.0),
        "cost_text": f"{_as_float(plan.get('cost_eur') or plan.get('estimated_cost_eur'), 0.0):.2f}",
        "saved_after_draw": plan.get("saved_after_draw", {}) or {},
        "plan_source": "v94_active_budget_plan",
        "plan_label_bg": "бюджетен план",
    }


def _v95_snapshot() -> dict[str, Any]:
    payload = _read_json(V95_MODEL)
    result = payload.get("result", {}) if isinstance(payload.get("result", {}), dict) else {}
    status = payload.get("status") or result.get("status") or "UNKNOWN"
    history_rows = _read_csv(V95_HISTORY)
    summary = result.get("summary", {}) if isinstance(result.get("summary", {}), dict) else {}
    return {
        "status": status,
        "evaluation_type": result.get("evaluation_type", ""),
        "message_bg": result.get("message_bg", payload.get("message_bg", "")),
        "history_rows": len(history_rows),
        "latest_best_hit_count": summary.get("best_hit_count", 0),
        "latest_rows_with_3_plus": summary.get("rows_with_3_plus", 0),
        "latest_rows_with_4_plus": summary.get("rows_with_4_plus", 0),
    }


def _v96_snapshot() -> dict[str, Any]:
    payload = _read_json(V96_MODEL)
    current = payload.get("current_snapshot", {}) if isinstance(payload.get("current_snapshot", {}), dict) else {}
    return {
        "status": payload.get("status", "UNKNOWN"),
        "maintenance_step": payload.get("maintenance_step", ""),
        "workflow_step_count": len(payload.get("workflow_steps", []) or []),
        "active_plan_type": current.get("active_plan_type", ""),
        "active_plan_combinations": current.get("active_plan_combinations", 0),
        "active_plan_cost_text": current.get("active_plan_cost_text", "0.00"),
        "active_plan_snapshot_source": current.get("active_plan_snapshot_source", ""),
        "active_plan_label_bg": current.get("active_plan_label_bg", ""),
        "v95_status": current.get("v95_status", "UNKNOWN"),
    }


def _add_draw_wiring_snapshot() -> dict[str, Any]:
    text = ADD_DRAWS_SECTION.read_text(encoding="utf-8", errors="replace") if ADD_DRAWS_SECTION.exists() else ""
    v95_index = text.find("evaluation = evaluate_active_plan_against_pending_draw")
    save_index = text.find("saved_count = save_draws(")
    # Step 106: Step 102 changed refresh_models to accept mode/timeout arguments.
    # Detect both the old exact call and the current argument-based call.
    refresh_candidates = [
        text.find("model_results = refresh_models("),
        text.find("refresh_models("),
        text.find("refresh_models()"),
    ]
    refresh_index = next((idx for idx in refresh_candidates if idx >= 0), -1)
    v97_script_present = "v97_build_real_draw_lifecycle.py" in text
    return {
        "add_draw_file_exists": ADD_DRAWS_SECTION.exists(),
        "v95_pre_save_reference": v95_index >= 0,
        "save_draws_reference": save_index >= 0,
        "v95_before_save_draws": v95_index >= 0 and save_index >= 0 and v95_index < save_index,
        "refresh_after_save_reference": refresh_index >= 0 and save_index >= 0 and refresh_index > save_index,
        "v97_refresh_script_present": v97_script_present,
    }


def _anti_backfit_snapshot() -> dict[str, Any]:
    text = V95_ENGINE.read_text(encoding="utf-8", errors="replace") if V95_ENGINE.exists() else ""
    return {
        "v95_engine_exists": V95_ENGINE.exists(),
        "draw_not_after_marker": "DRAW_NOT_AFTER_ACTIVE_PLAN" in text,
        "waiting_next_draw_marker": "WAITING_NEXT_DRAW" in text,
        "is_draw_after_saved_guard": "_is_draw_after_saved" in text,
        "history_duplicate_guard": "_history_has_draw" in text,
    }


def _readiness_status(plan: dict[str, Any], v95: dict[str, Any], wiring: dict[str, Any], anti_backfit: dict[str, Any]) -> tuple[str, list[str]]:
    issues: list[str] = []
    if not plan.get("active_plan_available"):
        issues.append("Няма активен план за следващ реален тираж.")
    if v95.get("status") not in {"WAITING_NEXT_DRAW", "EVALUATED", "DRAW_NOT_AFTER_ACTIVE_PLAN", "NO_ACTIVE_PLAN"}:
        issues.append(f"Step 95 статусът е неочакван: {v95.get('status')}")
    if not wiring.get("v95_before_save_draws"):
        issues.append("Add Draw не показва сигурен ред Step 95 преди save_draws.")
    if not wiring.get("refresh_after_save_reference"):
        issues.append("Add Draw не показва refresh след save_draws.")
    if not wiring.get("v97_refresh_script_present"):
        issues.append("Step 97 build script още не е включен във refresh chain.")
    if not anti_backfit.get("draw_not_after_marker") or not anti_backfit.get("is_draw_after_saved_guard"):
        issues.append("Anti-backfit guard markers липсват в Step 95 engine.")
    return ("READY" if not issues else "REVIEW"), issues


def build_real_draw_lifecycle_model() -> dict[str, Any]:
    V97_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    datasets = [_dataset_stats(path) for path in DATASET_PATHS]
    primary_dataset = datasets[0] if datasets else {}
    plan = _active_plan_snapshot()
    v95 = _v95_snapshot()
    v96 = _v96_snapshot()
    wiring = _add_draw_wiring_snapshot()
    anti_backfit = _anti_backfit_snapshot()
    readiness_status, issues = _readiness_status(plan, v95, wiring, anti_backfit)

    payload = {
        "step": 97,
        "status": readiness_status,
        "title_bg": "Реален цикъл на нов тираж",
        "generated_at_utc": _now_iso(),
        "safe_note_bg": SAFE_NOTE_BG,
        "current_state": {
            "dataset_rows": primary_dataset.get("rows", 0),
            "latest_draw_date": primary_dataset.get("latest_date", ""),
            "latest_draw_numbers": primary_dataset.get("latest_numbers", ""),
            "active_plan": plan,
            "step95": v95,
            "step96": v96,
            "add_draw_wiring": wiring,
            "anti_backfit": anti_backfit,
        },
        "datasets": datasets,
        "lifecycle_steps": LIFECYCLE_ROWS,
        "artifact_map": ARTIFACT_ROWS,
        "issues": issues,
        "next_user_action_bg": (
            "Когато излезе нов реален тираж, въведи числата в Добавяне на тираж. "
            "Системата първо ще оцени активния план и пакета, после ще запише тиража и ще обнови веригата."
            if readiness_status == "READY" else
            "Прегледай предупрежденията преди следващ реален тираж."
        ),
    }

    _write_json(MODEL_JSON, payload)
    _write_json(SUMMARY_JSON, {
        "step": 97,
        "status": readiness_status,
        "dataset_rows": primary_dataset.get("rows", 0),
        "latest_draw_date": primary_dataset.get("latest_date", ""),
        "latest_draw_numbers": primary_dataset.get("latest_numbers", ""),
        "active_plan_available": plan.get("active_plan_available", False),
        "active_plan_type": plan.get("strategy_type", ""),
        "active_plan_combinations": plan.get("combination_count", 0),
        "active_plan_cost_eur": plan.get("cost_eur", 0.0),
        "active_plan_cost_text": plan.get("cost_text", "0.00"),
        "active_plan_source": plan.get("plan_source", ""),
        "active_plan_label_bg": plan.get("plan_label_bg", ""),
        "step95_status": v95.get("status", "UNKNOWN"),
        "step96_status": v96.get("status", "UNKNOWN"),
        "v95_before_save_draws": wiring.get("v95_before_save_draws", False),
        "refresh_after_save": wiring.get("refresh_after_save_reference", False),
        "v97_refresh_script_present": wiring.get("v97_refresh_script_present", False),
        "anti_backfit_guard_ok": bool(anti_backfit.get("draw_not_after_marker") and anti_backfit.get("is_draw_after_saved_guard")),
        "issues_count": len(issues),
        "safe_note_bg": SAFE_NOTE_BG,
    })
    _write_csv(CHECKLIST_CSV, LIFECYCLE_ROWS, ["step_order", "phase_bg", "page_bg", "action_bg", "expected_artifact_bg", "guard_bg", "status_rule_bg"])
    _write_csv(ARTIFACTS_CSV, ARTIFACT_ROWS, ["artifact_group", "path", "purpose_bg", "owner_step"])

    lines = [
        "# Step 97 — Реален цикъл на нов тираж",
        "",
        payload["safe_note_bg"],
        "",
        "## Текущо състояние",
        "",
        f"- Статус: **{readiness_status}**",
        f"- Dataset редове: **{primary_dataset.get('rows', 0)}**",
        f"- Последен тираж: **{primary_dataset.get('latest_date', '')}** — **{primary_dataset.get('latest_numbers', '')}**",
        f"- Активен план: **{'Да' if plan.get('active_plan_available') else 'Не'}**",
        f"- Източник: **{plan.get('plan_label_bg', 'бюджетен план')}**",
        f"- Тип план: **{plan.get('strategy_type', '')}**",
        f"- Комбинации: **{plan.get('combination_count', 0)}**",
        f"- Цена: **{plan.get('cost_text', '0.00')} EUR**",
        f"- Step 95 статус: **{v95.get('status', 'UNKNOWN')}**",
        "",
        "## Последователност",
        "",
    ]
    for row in LIFECYCLE_ROWS:
        lines.extend([
            f"### {row['step_order']}. {row['phase_bg']}",
            "",
            f"- Страница: {row['page_bg']}",
            f"- Действие: {row['action_bg']}",
            f"- Контрол: {row['guard_bg']}",
            "",
        ])
    if issues:
        lines.extend(["## Елементи за преглед", ""])
        for issue in issues:
            lines.append(f"- {issue}")
        lines.append("")
    lines.extend(["## Следващо действие", "", payload["next_user_action_bg"], ""])
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")

    return payload


def build_and_save() -> dict[str, Any]:
    return build_real_draw_lifecycle_model()


def load_real_draw_lifecycle_summary() -> dict[str, Any]:
    if MODEL_JSON.exists():
        payload = _read_json(MODEL_JSON)
        if payload.get("lifecycle_steps"):
            return payload
    return build_real_draw_lifecycle_model()


if __name__ == "__main__":
    result = build_and_save()
    state = result.get("current_state", {}) or {}
    plan = state.get("active_plan", {}) or {}
    print("STEP_97_STATUS", result.get("status", "UNKNOWN"))
    print("DATASET_ROWS", state.get("dataset_rows", 0))
    print("ACTIVE_PLAN", plan.get("strategy_type", "-"), plan.get("combination_count", 0), plan.get("cost_text", "0.00"))
