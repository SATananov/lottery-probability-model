from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v95_active_plan_auto_evaluation_engine import build_and_save


if __name__ == "__main__":
    payload = build_and_save()
    summary = payload.get("summary", {}) or {}
    print("STEP_95_STATUS", payload.get("status", "UNKNOWN"))
    print("EVALUATION_TYPE", payload.get("evaluation_type", "-"))
    print("BEST_HITS", summary.get("best_hit_count", 0))
