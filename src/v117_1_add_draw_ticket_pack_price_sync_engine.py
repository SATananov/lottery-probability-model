from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"

V117_SUMMARY = REPORTS_DIR / "v117_real_ticket_pack_builder_summary.json"
V96_MODEL = MODELS_DIR / "v96" / "v96_add_draw_controlled_flow_model.json"
V97_MODEL = MODELS_DIR / "v97" / "v97_real_draw_lifecycle_model.json"
ADD_DRAW_SECTION = ROOT / "src" / "add_draws_section.py"

MODEL_JSON = MODELS_DIR / "v117_1" / "add_draw_ticket_pack_price_sync_status.json"
REPORT_JSON = REPORTS_DIR / "v117_1_add_draw_ticket_pack_price_sync_report.json"
REPORT_MD = REPORTS_DIR / "v117_1_add_draw_ticket_pack_price_sync_report.md"

EXPECTED_LINES = 12
EXPECTED_PRICE_EUR = 10.80


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


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip().replace(",", ".")))
    except Exception:
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip().replace(",", "."))
    except Exception:
        return default


def _check(name: str, ok: bool, details: str) -> dict[str, Any]:
    return {
        "check": name,
        "status": "OK" if ok else "BLOCKING",
        "blocking": not ok,
        "details": details,
    }


def build_add_draw_ticket_pack_price_sync() -> dict[str, Any]:
    v117 = _read_json(V117_SUMMARY)
    v96 = _read_json(V96_MODEL)
    v97 = _read_json(V97_MODEL)

    v96_snapshot = v96.get("current_snapshot", {}) if isinstance(v96.get("current_snapshot", {}), dict) else {}
    v97_state = v97.get("current_state", {}) if isinstance(v97.get("current_state", {}), dict) else {}
    v97_plan = v97_state.get("active_plan", {}) if isinstance(v97_state.get("active_plan", {}), dict) else {}

    add_draw_text = ADD_DRAW_SECTION.read_text(encoding="utf-8", errors="replace") if ADD_DRAW_SECTION.exists() else ""

    checks = [
        _check(
            "v117_total_lines_is_12",
            _as_int(v117.get("total_lines"), 0) == EXPECTED_LINES,
            f"v117 total_lines={v117.get('total_lines')}",
        ),
        _check(
            "v117_total_price_is_10_80",
            round(_as_float(v117.get("total_price_eur"), 0.0), 2) == EXPECTED_PRICE_EUR,
            f"v117 total_price_eur={v117.get('total_price_eur')}",
        ),
        _check(
            "v96_add_draw_snapshot_uses_12_lines",
            _as_int(v96_snapshot.get("active_plan_combinations"), 0) == EXPECTED_LINES,
            f"v96 active_plan_combinations={v96_snapshot.get('active_plan_combinations')}",
        ),
        _check(
            "v96_add_draw_snapshot_uses_10_80",
            round(_as_float(v96_snapshot.get("active_plan_cost_eur"), 0.0), 2) == EXPECTED_PRICE_EUR,
            f"v96 active_plan_cost_eur={v96_snapshot.get('active_plan_cost_eur')}",
        ),
        _check(
            "v97_lifecycle_plan_uses_12_lines",
            _as_int(v97_plan.get("combination_count"), 0) == EXPECTED_LINES,
            f"v97 combination_count={v97_plan.get('combination_count')}",
        ),
        _check(
            "v97_lifecycle_plan_uses_10_80",
            round(_as_float(v97_plan.get("cost_eur"), 0.0), 2) == EXPECTED_PRICE_EUR,
            f"v97 cost_eur={v97_plan.get('cost_eur')}",
        ),
        _check(
            "add_draw_info_label_is_generic_pack_label",
            "active_plan_label_bg" in add_draw_text and "Активният {active_plan_label}" in add_draw_text,
            "Add Draw reads active_plan_label_bg instead of hard-coded budget-plan text.",
        ),
    ]

    blocking_failures = sum(1 for item in checks if item["blocking"])
    status = "ADD_DRAW_TICKET_PACK_PRICE_SYNC_READY" if blocking_failures == 0 else "ADD_DRAW_TICKET_PACK_PRICE_SYNC_REVIEW"

    payload = {
        "step": "117.1",
        "name": "Step 117.1 — Add Draw Ticket Pack Price Sync",
        "status": status,
        "blocking_failures": blocking_failures,
        "expected_lines": EXPECTED_LINES,
        "expected_total_price_eur": EXPECTED_PRICE_EUR,
        "v117_total_lines": _as_int(v117.get("total_lines"), 0),
        "v117_total_price_eur": round(_as_float(v117.get("total_price_eur"), 0.0), 2),
        "v96_active_plan_combinations": _as_int(v96_snapshot.get("active_plan_combinations"), 0),
        "v96_active_plan_cost_eur": round(_as_float(v96_snapshot.get("active_plan_cost_eur"), 0.0), 2),
        "v97_active_plan_combinations": _as_int(v97_plan.get("combination_count"), 0),
        "v97_active_plan_cost_eur": round(_as_float(v97_plan.get("cost_eur"), 0.0), 2),
        "checks": checks,
        "safe_note_bg": "Hotfix слой: синхронизира визуалния Add Draw статус с реалния Step 117 пакет. Не променя числата и не обещава печалба.",
    }

    _write_json(MODEL_JSON, payload)
    _write_json(REPORT_JSON, payload)

    md_lines = [
        "# Step 117.1 — Add Draw Ticket Pack Price Sync",
        "",
        payload["safe_note_bg"],
        "",
        f"- Status: `{status}`",
        f"- Blocking failures: `{blocking_failures}`",
        f"- Очаквани редове: `{EXPECTED_LINES}`",
        f"- Очаквана цена: `{EXPECTED_PRICE_EUR:.2f} EUR`",
        f"- Add Draw snapshot: `{payload['v96_active_plan_combinations']}` реда / `{payload['v96_active_plan_cost_eur']:.2f} EUR`",
        f"- Lifecycle snapshot: `{payload['v97_active_plan_combinations']}` реда / `{payload['v97_active_plan_cost_eur']:.2f} EUR`",
        "",
        "## Проверки",
        "",
    ]
    for check in checks:
        md_lines.append(f"- `{check['status']}` — {check['check']}: {check['details']}")
    REPORT_MD.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")

    return payload


def print_summary(payload: dict[str, Any]) -> None:
    print(f"STEP_117_1_STATUS {payload.get('status')}")
    print(f"BLOCKING_FAILURES {payload.get('blocking_failures')}")
    print(f"ADD_DRAW_LINES {payload.get('v96_active_plan_combinations')}")
    print(f"ADD_DRAW_PRICE_EUR {payload.get('v96_active_plan_cost_eur')}")
    print(f"BAD_COUNT {payload.get('blocking_failures')}")
