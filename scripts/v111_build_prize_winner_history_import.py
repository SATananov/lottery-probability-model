from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_prize_winner_history_engine import write_artifacts


def build_step() -> dict:
    summary = write_artifacts()
    print(f"STEP_111_STATUS {summary.get('status')}")
    print(f"BLOCKING_FAILURES {summary.get('blocking_failures')}")
    print(f"OFFICIAL_SOURCE {summary.get('official_source')}")
    print(f"IMPORTED_DRAWS {summary.get('imported_draws')}")
    latest = summary.get("latest_record") or {}
    if latest:
        print(f"LATEST_PRIZE_DRAW {latest.get('draw_date')} {latest.get('draw_number')} {latest.get('numbers_text')}")
    else:
        print("LATEST_PRIZE_DRAW none")
    return summary


if __name__ == "__main__":
    build_step()
