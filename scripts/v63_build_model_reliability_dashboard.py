from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v63_model_reliability_dashboard_engine import build_model_reliability_dashboard


if __name__ == "__main__":
    summary = build_model_reliability_dashboard()
    print("STEP63_BUILD_OK")
    print("HISTORY_ROWS", summary.get("history_rows"))
    print("TRACKED_DRAWS", summary.get("tracked_draws"))
    print("MODELS_RANKED", summary.get("models_ranked"))
    print("BEST_MODEL", summary.get("best_model_label"))
    print("BEST_SCORE", summary.get("best_reliability_score"))
