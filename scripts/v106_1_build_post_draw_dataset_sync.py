from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v106_1_post_draw_dataset_sync_engine import build_post_draw_dataset_sync

if __name__ == "__main__":
    result = build_post_draw_dataset_sync(run_dependencies=True)
    print("STEP_106_1_STATUS", result.get("status"))
    print("BLOCKING_FAILURES", result.get("blocking_failures"))
    dataset = result.get("dataset", {}) or {}
    print("DATASET_ROWS", dataset.get("rows"))
    print("ROW_COUNTS", dataset.get("row_counts"))
    print("LATEST_DRAW", dataset.get("latest_date"), dataset.get("latest_numbers"))
