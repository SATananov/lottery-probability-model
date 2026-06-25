from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v107_model_training_policy_engine import write_artifacts


def main() -> None:
    summary = write_artifacts()
    print("STEP_107_STATUS", summary.get("status", "UNKNOWN"))
    print("BLOCKING_FAILURES", summary.get("blocking_failures", 0))
    print("DATASET_ROWS", summary.get("dataset", {}).get("dataset_rows", 0))
    print("REAL_RESULT_ROWS", summary.get("real_result_rows_since_active_plan", 0))
    print("RECOMMENDATION", summary.get("policy_decision", {}).get("label_bg", ""))


if __name__ == "__main__":
    main()
