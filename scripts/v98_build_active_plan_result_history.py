from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v98_active_plan_result_history_engine import build_and_save


if __name__ == "__main__":
    payload = build_and_save()
    plan = payload.get("active_plan", {}) or {}
    summary = payload.get("history_summary", {}) or {}
    print("STEP_98_STATUS", payload.get("status", "UNKNOWN"))
    print("ACTIVE_PLAN", plan.get("strategy_type", "-"), plan.get("combination_count", 0), plan.get("cost_text", "0.00"))
    print("HISTORY_ROWS", summary.get("real_result_rows", 0))
