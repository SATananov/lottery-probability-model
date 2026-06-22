from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v68_weighted_portfolio_optimizer_engine import build_weighted_portfolio_optimizer


if __name__ == "__main__":
    summary = build_weighted_portfolio_optimizer()
    print("STEP68_BUILD_OK")
    print("TICKETS_ANALYZED", summary.get("tickets_analyzed"))
    print("UNIQUE_NUMBERS_COVERED", summary.get("unique_numbers_covered"))
    print("PORTFOLIO_SCORE", summary.get("portfolio_score"))
    print("PORTFOLIO_STATUS", summary.get("portfolio_status"))
