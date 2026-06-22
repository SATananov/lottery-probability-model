from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v79_ticket_pack_export_engine import build_ticket_pack_export_center

if __name__ == "__main__":
    summary = build_ticket_pack_export_center()
    print("STEP79_BUILD_OK")
    print("STATUS", summary.get("status"))
    print("VALID_DRAWS", summary.get("valid_draws"))
    print("CANDIDATES", summary.get("candidate_tickets"))
    print("PLAY_TICKETS", summary.get("play_tickets"))
    print("RESERVE_TICKETS", summary.get("reserve_tickets"))
    print("BEST_TICKET", summary.get("best_ticket_id"))
