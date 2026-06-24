from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v96" / "v96_add_draw_controlled_flow_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v96_add_draw_controlled_flow_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v96_add_draw_controlled_flow_summary.md"
CHECKLIST_CSV_PATH = ROOT / "reports" / "v96_add_draw_controlled_flow_checklist.csv"

V94_MODEL_PATH = ROOT / "models" / "v94" / "v94_active_budget_plan_tracker_model.json"
V95_MODEL_PATH = ROOT / "models" / "v95" / "v95_active_plan_auto_evaluation_model.json"

SAFE_NOTE_BG = (
    "Step 96 е UX/control слой за страницата Добавяне на тираж. "
    "Той не променя прогнозните модели и не обещава печалба; целта е правилен ред на действията."
)

WORKFLOW_STEPS: list[dict[str, Any]] = [
    {
        "step_order": 1,
        "title_bg": "Провери активния бюджетен план",
        "when_bg": "Преди запис на новия тираж",
        "description_bg": "Step 95 използва същите въведени числа и проверява активния Step 94 план преди dataset refresh.",
        "guard_bg": "Не допуска backfit към стар или същия тираж.",
    },
    {
        "step_order": 2,
        "title_bg": "Провери текущия пакет",
        "when_bg": "Преди запис на новия тираж",
        "description_bg": "Step 73 проверява активния пакет срещу въведените числа.",
        "guard_bg": "Оценката се прави преди данните да станат част от dataset-а.",
    },
    {
        "step_order": 3,
        "title_bg": "Валидирай и запиши тиража",
        "when_bg": "След pre-save проверките",
        "description_bg": "Системата записва новия тираж само след успешни проверки и валидни 6 различни числа.",
        "guard_bg": "Грешна или непълна комбинация спира записа.",
    },
    {
        "step_order": 4,
        "title_bg": "Обнови dataset-а",
        "when_bg": "След успешен запис",
        "description_bg": "Новият тираж вече става част от историческите данни.",
        "guard_bg": "Редът пази разликата между предишен план и нов резултат.",
    },
    {
        "step_order": 5,
        "title_bg": "Refresh на моделите",
        "when_bg": "След dataset update",
        "description_bg": "Изпълнява се избраната верига за обновяване на моделите и отчетите.",
        "guard_bg": "Step 94/95 се обновяват в правилен ред за следващи проверки.",
    },
    {
        "step_order": 6,
        "title_bg": "Контрол и синхрон",
        "when_bg": "След refresh",
        "description_bg": "GitHub sync и dependency контролът потвърждават, че app, reports и models са в синхрон.",
        "guard_bg": "Финалният status трябва да е чист преди clean ZIP checkpoint.",
    },
]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["step_order", "title_bg", "when_bg", "description_bg", "guard_bg"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def _first_present(mapping: dict[str, Any], keys: list[str], default: Any = "") -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _current_snapshot() -> dict[str, Any]:
    v94_payload = _read_json(V94_MODEL_PATH)
    v95_payload = _read_json(V95_MODEL_PATH)

    active_plan = _find_active_plan(v94_payload)
    v95_result = v95_payload.get("result", {}) if isinstance(v95_payload.get("result", {}), dict) else {}

    active_plan_type = ""
    active_plan_combinations = 0
    active_plan_cost_eur = 0.0

    if active_plan:
        active_plan_type = str(
            _first_present(
                active_plan,
                ["strategy_type", "recommended_type", "plan_type", "preference_label"],
                "",
            )
        )
        active_plan_combinations = _as_int(
            _first_present(active_plan, ["combination_count", "recommended_combinations", "max_budget_combinations"], 0),
            0,
        )
        active_plan_cost_eur = _as_float(
            _first_present(active_plan, ["cost_eur", "estimated_cost_eur", "total_cost_eur"], 0.0),
            0.0,
        )

    return {
        "active_plan_available": bool(active_plan),
        "active_plan_type": active_plan_type,
        "active_plan_combinations": active_plan_combinations,
        "active_plan_cost_eur": active_plan_cost_eur,
        "active_plan_cost_text": f"{active_plan_cost_eur:.2f}",
        "v95_status": v95_payload.get("status") or v95_result.get("status", "UNKNOWN"),
        "v95_expected_state_before_next_draw": "WAITING_NEXT_DRAW",
        "step96_1_fix_bg": "Step 96.1 коригира четенето на активния Step 94 план: strategy_type/cost_eur вместо празни legacy ключове.",
        "add_draw_rule_bg": "Въведените числа в Добавяне на тираж са единственият вход за Step 95 проверката.",
    }


def build_add_draw_controlled_flow_model() -> dict[str, Any]:
    snapshot = _current_snapshot()

    payload = {
        "step": 96,
        "maintenance_step": "96.1",
        "status": "OK",
        "title_bg": "Контролиран ред при добавяне на тираж",
        "intro_bg": (
            "Тази секция показва точния ред на действията при добавяне на нов тираж. "
            "Целта е първо да се оцени активният план срещу новите числа, после да се записва и обновява."
        ),
        "workflow_steps": WORKFLOW_STEPS,
        "current_snapshot": snapshot,
        "safe_note_bg": SAFE_NOTE_BG,
    }

    _write_json(MODEL_PATH, payload)
    _write_json(SUMMARY_JSON_PATH, {
        "step": 96,
        "maintenance_step": "96.1",
        "status": "OK",
        "workflow_step_count": len(WORKFLOW_STEPS),
        "active_plan_available": snapshot.get("active_plan_available", False),
        "active_plan_type": snapshot.get("active_plan_type", ""),
        "active_plan_combinations": snapshot.get("active_plan_combinations", 0),
        "active_plan_cost_eur": snapshot.get("active_plan_cost_eur", 0.0),
        "active_plan_cost_text": snapshot.get("active_plan_cost_text", "0.00"),
        "v95_status": snapshot.get("v95_status", "UNKNOWN"),
        "safe_note_bg": SAFE_NOTE_BG,
    })
    _write_csv(CHECKLIST_CSV_PATH, WORKFLOW_STEPS)

    lines = [
        "# Step 96 — Контролиран ред при добавяне на тираж",
        "",
        payload["intro_bg"],
        "",
    ]
    for step in WORKFLOW_STEPS:
        lines.extend([
            f"## {step['step_order']}. {step['title_bg']}",
            "",
            f"- Кога: {step['when_bg']}",
            f"- Какво прави: {step['description_bg']}",
            f"- Контрол: {step['guard_bg']}",
            "",
        ])
    lines.extend([
        "## Текущо състояние",
        "",
        f"- Активен план: {'Да' if snapshot.get('active_plan_available') else 'Не'}",
        f"- Тип план: {snapshot.get('active_plan_type', '')}",
        f"- Комбинации: {snapshot.get('active_plan_combinations', 0)}",
        f"- Цена: {snapshot.get('active_plan_cost_text', '0.00')} EUR",
        f"- Step 95 статус: {snapshot.get('v95_status', 'UNKNOWN')}",
        "",
        SAFE_NOTE_BG,
    ])
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return payload


def build_and_save() -> dict[str, Any]:
    return build_add_draw_controlled_flow_model()


def load_add_draw_controlled_flow_summary() -> dict[str, Any]:
    if MODEL_PATH.exists():
        payload = _read_json(MODEL_PATH)
        if payload.get("workflow_steps"):
            return payload
    return {
        "step": 96,
        "maintenance_step": "96.1",
        "status": "FALLBACK",
        "title_bg": "Контролиран ред при добавяне на тираж",
        "intro_bg": "Първо се правят pre-save проверки, после се записва тиражът и се обновяват моделите.",
        "workflow_steps": WORKFLOW_STEPS,
        "current_snapshot": _current_snapshot(),
        "safe_note_bg": SAFE_NOTE_BG,
    }


if __name__ == "__main__":
    payload = build_and_save()
    snapshot = payload.get("current_snapshot", {}) or {}
    print("STEP_96_STATUS", payload.get("status", "UNKNOWN"))
    print("WORKFLOW_STEPS", len(payload.get("workflow_steps", []) or []))
    print("V95_STATUS", snapshot.get("v95_status", "UNKNOWN"))
