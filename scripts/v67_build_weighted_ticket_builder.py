from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v67_weighted_ticket_builder_engine import build_weighted_ticket_builder


if __name__ == "__main__":
    summary = build_weighted_ticket_builder()
    print("STEP67_BUILD_OK")
    print("TICKETS_GENERATED", summary.get("tickets_generated"))
    print("TOP_TICKET_ID", summary.get("top_average_weighted_score_ticket_id"))
    print("TOP_AVG_SCORE", summary.get("top_average_weighted_score"))
