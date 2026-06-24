from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v103_1_clean_zip_metadata_finalizer_engine import build_and_write_metadata_finalizer_summary


def main() -> None:
    summary = build_and_write_metadata_finalizer_summary()
    print("STEP_103_1_STATUS", summary.get("status"))
    print("BLOCKING_FAILURES", summary.get("blocking_failures"))


if __name__ == "__main__":
    main()
