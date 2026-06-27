from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_8_verified_2026_prize_history_import import import_verified_2026_history, print_status


def main() -> None:
    summary = import_verified_2026_history(clean_invalid_existing_rows=True)
    print_status(summary)
    if int(summary.get("blocking_failures", 0) or 0) != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
