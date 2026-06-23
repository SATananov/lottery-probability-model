
from __future__ import annotations

import json
from pathlib import Path

MODEL_PATH = Path("models/v89/v89_final_statistical_portfolio_selector_model.json")


def main() -> int:
    if not MODEL_PATH.exists():
        print("STEP_89_1_STATUS MISSING_V89_MODEL")
        return 1
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8-sig"))
    balanced = model.get("balanced_recommendation") or model.get("recommendations", {}).get("balanced", {})
    print("STEP_89_1_STATUS OK")
    print(f"BALANCED_PACKAGE {balanced.get('package_id', '')}")
    print(f"BALANCED_COMBINATIONS {len(balanced.get('combinations', []))}")
    print(f"BALANCED_UNIQUE_NUMBERS {balanced.get('unique_covered_numbers', 0)}")
    print(f"BALANCED_EMPTY_RISK_PERCENT {balanced.get('empty_risk_percent', 0.0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
