from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v76_explainability_validation_engine import build_explainability_validation_center

if __name__ == "__main__":
    summary = build_explainability_validation_center()
    print("STEP76_BUILD_OK")
    print("STATUS", summary.get("status"))
    print("VALID_DRAWS", summary.get("valid_draws"))
    print("NUMBERS_EXPLAINED", summary.get("numbers_explained"))
    print("TICKETS_VALIDATED", summary.get("tickets_validated"))
    print("WARNING_ITEMS", summary.get("warning_items"))
