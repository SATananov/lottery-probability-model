from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v94_active_budget_plan_tracker_engine import build_and_save


if __name__ == "__main__":
    result = build_and_save()
    plan = result.get("active_plan", {}) or {}
    status = (result.get("result", {}) or {}).get("status", "-")
    demo_best = ((result.get("demo_result", {}) or {}).get("summary", {}) or {}).get("best_hit_count", 0)
    print("STEP_94_STATUS", result.get("status", "UNKNOWN"))
    print("ACTIVE_PLAN", plan.get("strategy_type", "-"), plan.get("combination_count", 0), f"{float(plan.get('cost_eur', 0.0)):.2f}")
    print("RESULT_STATUS", status)
    print("DEMO_BEST_HITS", demo_best)
