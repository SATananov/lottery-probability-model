from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v89_final_statistical_portfolio_selector_engine import build_and_save


def main() -> int:
    model = build_and_save()
    balanced = model.get("balanced_recommendation", {})
    print("STEP_89_STATUS OK")
    print(f"CANDIDATE_PACKAGES {model.get('candidate_count', 0)}")
    print(f"BALANCED_PACKAGE {balanced.get('package_id', '')}")
    print(f"BALANCED_SCORE {balanced.get('mode_scores', {}).get('balanced', 0.0)}")
    print(f"BALANCED_UNIQUE_NUMBERS {balanced.get('unique_covered_numbers', 0)}")
    print(f"BALANCED_EMPTY_RISK_PERCENT {balanced.get('empty_risk_percent', 0.0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
