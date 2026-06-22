from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v62_model_performance_tracker_engine import build_model_performance_tracker


if __name__ == "__main__":
    summary = build_model_performance_tracker()
    print("STEP62_BUILD_OK")
    print("TOTAL_DRAWS", summary.get("total_draws"))
    print("LATEST_DRAW", summary.get("latest_draw"))
    print("MODELS_EVALUATED", summary.get("models_evaluated"))
    print("BEST_HITS", summary.get("best_hits"))
