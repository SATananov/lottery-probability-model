from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v103_clean_release_checkpoint_engine import build_and_write_clean_release_summary


def main() -> None:
    summary = build_and_write_clean_release_summary()
    print("STEP_103_STATUS", summary.get("status"))
    print("TRACKED_FILES", summary.get("tracked_file_count"))
    print("FORBIDDEN_TRACKED", summary.get("forbidden_tracked_count"))
    print("BLOCKING_FAILURES", summary.get("blocking_failures"))
    print("NEXT_ACTION", summary.get("recommended_command"))


if __name__ == "__main__":
    main()
