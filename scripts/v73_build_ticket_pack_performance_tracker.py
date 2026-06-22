from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v73_ticket_pack_performance_tracker_engine import build_ticket_pack_performance_tracker


if __name__ == "__main__":
    summary = build_ticket_pack_performance_tracker()
    print("STEP73_BUILD_OK")
    print("ACTIVE_PACK_TICKETS", summary.get("active_pack_tickets"))
    print("HISTORY_ROWS", summary.get("history_rows"))
    print("STATUS", summary.get("status"))
