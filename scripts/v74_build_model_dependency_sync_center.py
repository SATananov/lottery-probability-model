from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v74_model_dependency_sync_center_engine import build_model_dependency_sync_center


if __name__ == "__main__":
    summary = build_model_dependency_sync_center()
    print("STEP74_BUILD_OK")
    print("STATUS", summary.get("status"))
    print("MODELS_CHECKED", summary.get("models_checked"))
    print("SYNCED_MODELS", summary.get("synced_models"))
    print("STALE_MODELS", summary.get("stale_models"))
    print("MISSING_MODELS", summary.get("missing_models"))
