from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v109_sqlite_journal_engine import write_artifacts


def build_step() -> dict:
    summary = write_artifacts(sync_latest_draw=True, evaluate_open=True)
    latest = summary.get("latest_journal_draw") or summary.get("latest_dataset_draw") or {}
    print(f"STEP_109_STATUS {summary.get('status')}")
    print(f"BLOCKING_FAILURES {summary.get('blocking_failures')}")
    print(f"DB_PATH {summary.get('database_path')}")
    print(f"DRAW_ENTRIES {summary.get('counts', {}).get('draw_entries')}")
    print(f"PLAYED_TICKETS {summary.get('counts', {}).get('played_tickets')}")
    print(f"LATEST_DRAW {latest.get('draw_date') or latest.get('date')} {latest.get('numbers') or latest.get('numbers_text')}")
    return summary


if __name__ == "__main__":
    build_step()
