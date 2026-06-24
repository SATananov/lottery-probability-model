from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v101_real_use_protocol_engine import build_and_save


if __name__ == "__main__":
    payload = build_and_save()
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    failures = payload.get("blocking_failures", []) or []
    print("STEP_101_STATUS", payload.get("status", "UNKNOWN"))
    print("STEP_100_STATUS", payload.get("step100_status", "UNKNOWN"))
    print("ACTIVE_PLAN", active_plan.get("strategy_type", "-"), active_plan.get("combination_count", 0), active_plan.get("cost_text", "-"))
    print("DATASET_ROWS", dataset.get("historical_rows", 0))
    print("BLOCKING_FAILURES", len(failures))
    print("NEXT_ACTION", payload.get("next_action_bg", "-"))
