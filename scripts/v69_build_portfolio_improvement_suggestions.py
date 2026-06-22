from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v69_portfolio_improvement_engine import build_portfolio_improvement_suggestions


if __name__ == "__main__":
    summary = build_portfolio_improvement_suggestions()
    print("STEP69_BUILD_OK")
    print("SUGGESTIONS_GENERATED", summary.get("suggestions_generated"))
    print("CANDIDATE_CHANGES", summary.get("candidate_changes_applied"))
    print("BASELINE_SCORE", summary.get("baseline_portfolio_score"))
    print("CANDIDATE_SCORE", summary.get("candidate_portfolio_score"))
