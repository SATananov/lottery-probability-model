from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v70_applied_candidate_portfolio_engine import build_applied_candidate_portfolio


if __name__ == "__main__":
    summary = build_applied_candidate_portfolio()
    print("STEP70_BUILD_OK")
    print("APPLIED_TICKETS", summary.get("applied_portfolio_tickets"))
    print("APPLIED_CHANGES", summary.get("applied_changes_count"))
    print("ORIGINAL_SCORE", summary.get("original_portfolio_score"))
    print("APPLIED_SCORE", summary.get("applied_portfolio_score"))
