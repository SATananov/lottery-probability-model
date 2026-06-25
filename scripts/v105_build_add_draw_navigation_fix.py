from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v105_add_draw_navigation_fix_engine import build_add_draw_navigation_fix

if __name__ == "__main__":
    result = build_add_draw_navigation_fix()
    print("STEP_105_STATUS", result.get("status"))
    print("BLOCKING_FAILURES", result.get("blocking_failures"))
