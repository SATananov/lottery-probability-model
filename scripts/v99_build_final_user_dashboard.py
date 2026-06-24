from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v99_final_user_dashboard_engine import build_and_save


if __name__ == "__main__":
    payload = build_and_save()
    active_plan = payload.get("active_plan", {}) or {}
    statuses = payload.get("statuses", {}) or {}
    next_action = payload.get("next_action", {}) or {}
    print("STEP_99_STATUS", payload.get("status", "UNKNOWN"))
    print("ACTIVE_PLAN", active_plan.get("strategy_type", "-"), active_plan.get("combination_count", 0), active_plan.get("cost_text", "0.00"))
    print("STEP_95", statuses.get("step95_status", "UNKNOWN"))
    print("NEXT_ACTION", next_action.get("title_bg", "-"))
