from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v71_ticket_pack_export_engine import build_ticket_pack_export


if __name__ == "__main__":
    summary = build_ticket_pack_export()
    print("STEP71_BUILD_OK")
    print("TICKETS_EXPORTED", summary.get("tickets_exported"))
    print("CHANGES_INCLUDED", summary.get("changes_included"))
    print("APPLIED_SCORE", summary.get("applied_portfolio_score"))
