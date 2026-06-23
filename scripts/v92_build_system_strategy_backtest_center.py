from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v92_system_strategy_backtest_center_engine import build_and_save


def main() -> int:
    model = build_and_save()
    best_under_10 = model.get("best_under_10_eur", {}) or {}
    best_four = model.get("best_four_combo_strategy", {}) or {}
    print("STEP_92_STATUS", model.get("status", "UNKNOWN"))
    print("DRAWS_TESTED", model.get("draws_tested", 0))
    print("STRATEGIES_TESTED", model.get("strategies_tested", 0))
    print("BEST_UNDER_10", best_under_10.get("combination_count", 0), best_under_10.get("budget_efficiency_score", 0.0))
    print("BEST_4_COMBO", best_four.get("combination_count", 0), best_four.get("budget_efficiency_score", 0.0))
    return 0 if model.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
