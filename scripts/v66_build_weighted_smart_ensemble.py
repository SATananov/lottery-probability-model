from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v66_weighted_smart_ensemble_engine import build_weighted_smart_ensemble


if __name__ == "__main__":
    summary = build_weighted_smart_ensemble()
    print("STEP66_BUILD_OK")
    print("SOURCES_USED", summary.get("sources_used"))
    print("NUMBERS_SCORED", summary.get("numbers_scored"))
    print("TOP_NUMBER", summary.get("top_number"))
    print("TOP_SCORE", summary.get("top_weighted_score_percent"))
