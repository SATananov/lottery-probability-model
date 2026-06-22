from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v65_model_weighting_engine import build_model_weighting_center


if __name__ == "__main__":
    summary = build_model_weighting_center()
    print("STEP65_BUILD_OK")
    print("MODELS_WEIGHTED", summary.get("models_weighted"))
    print("TOP_MODEL", summary.get("top_model_label"))
    print("TOP_WEIGHT", summary.get("top_adaptive_weight_percent"))
