from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v84_model_comparison_forward_test_engine import build_model_comparison_forward_test_center


if __name__ == "__main__":
    result = build_model_comparison_forward_test_center()
    print("STEP84_STATUS", result.get("status"))
    print("CANDIDATES", result.get("current_candidates"))
    print("SNAPSHOTS", result.get("snapshots_recorded"))
    print("EVALUATED_ROWS", result.get("evaluated_rows"))
    print("MODELS_COMPARED", result.get("models_compared"))
