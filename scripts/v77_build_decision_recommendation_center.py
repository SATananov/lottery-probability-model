from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v77_decision_recommendation_engine import build_decision_recommendation_center

if __name__ == "__main__":
    summary = build_decision_recommendation_center()
    print("STEP77_BUILD_OK")
    print("STATUS", summary.get("status"))
    print("VALID_DRAWS", summary.get("valid_draws"))
    print("RECOMMENDATIONS", summary.get("recommendations_count"))
    print("BEST_TICKET", summary.get("best_ticket_id"))
    print("BEST_SCORE", summary.get("best_decision_score"))
