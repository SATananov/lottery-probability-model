from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v91_budget_aware_system_builder_engine import build_and_save


def main() -> int:
    model = build_and_save()
    practical = model.get("practical_recommendation", {})
    print("STEP_91_STATUS OK")
    print(f"SYSTEM_OPTIONS {model.get('option_count', 0)}")
    print(f"PRACTICAL_COMBINATIONS {practical.get('selected_combinations', 0)}")
    print(f"PRACTICAL_SCORE {practical.get('system_score', 0.0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
