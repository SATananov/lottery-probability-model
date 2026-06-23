from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v93_budget_advisor_engine import build_and_save


def main() -> int:
    model = build_and_save()
    current = model.get("current_reference_advice", {}) or {}
    rec = current.get("recommendation", {}) or {}
    print("STEP_93_STATUS", model.get("status", "UNKNOWN"))
    print("DEFAULT_BUDGET", current.get("budget_eur", 0.0))
    print("MAX_COMBINATIONS", current.get("max_budget_combinations", 0))
    print("RECOMMENDED", rec.get("strategy_type", "-"), rec.get("combination_count", 0), f"{float(rec.get('advisor_score', 0.0)):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
