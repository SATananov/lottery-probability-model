from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v97_real_draw_lifecycle_engine import build_and_save


if __name__ == "__main__":
    payload = build_and_save()
    state = payload.get("current_state", {}) or {}
    plan = state.get("active_plan", {}) or {}
    print("STEP_97_STATUS", payload.get("status", "UNKNOWN"))
    print("DATASET_ROWS", state.get("dataset_rows", 0))
    print("ACTIVE_PLAN", plan.get("strategy_type", "-"), plan.get("combination_count", 0), plan.get("cost_text", "0.00"))
