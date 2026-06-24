from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v104_final_audit_refresh_engine import build_and_write_final_audit_refresh_summary


def main() -> None:
    summary = build_and_write_final_audit_refresh_summary()
    dataset = summary.get("dataset", {})
    print("STEP_104_STATUS", summary.get("status"))
    print("BLOCKING_FAILURES", summary.get("blocking_failures"))
    print("DATASET_ROWS", dataset.get("rows"))
    print("LATEST_DRAW", dataset.get("latest_date"), dataset.get("latest_numbers"))


if __name__ == "__main__":
    main()
