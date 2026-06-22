from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v78_final_play_plan_engine import build_final_play_plan_center

if __name__ == "__main__":
    summary = build_final_play_plan_center()
    print("STEP78_BUILD_OK")
    print("STATUS", summary.get("status"))
    print("VALID_DRAWS", summary.get("valid_draws"))
    print("CANDIDATES", summary.get("candidate_tickets"))
    print("ACTIVE_TICKETS", summary.get("active_tickets"))
    print("RESERVE_TICKETS", summary.get("reserve_tickets"))
    print("BEST_TICKET", summary.get("best_ticket_id"))
