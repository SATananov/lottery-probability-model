from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BAD_MARKERS = ["?" * 4, chr(0xFFFD)]


def main() -> int:
    from src.v112_prize_statistics_section import load_prize_history, write_statistics_reports

    stats = write_statistics_reports()
    blocking = 0
    df = load_prize_history()
    rows = int(stats.get("rows", 0) or 0)
    bad_count = 0
    checked_files = [
        ROOT / "src" / "v112_prize_statistics_section.py",
        ROOT / "scripts" / "v112_build_prize_statistics.py",
        ROOT / "reports" / "v112_prize_statistics_report.json",
        ROOT / "reports" / "v112_prize_statistics_report.md",
    ]
    for path in checked_files:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            bad_count += sum(text.count(marker) for marker in BAD_MARKERS)
    if bad_count:
        blocking += 1
    print("STEP_112_STATUS", stats.get("status", "UNKNOWN"))
    print("BLOCKING_FAILURES", blocking)
    print("PRIZE_HISTORY_ROWS", rows)
    print("SIX_WINNING_DRAWS", stats.get("six_winning_draws", 0))
    print("CURRENT_GAP_AFTER_LAST_SIX", stats.get("current_gap_after_last_six"))
    print("CONFIDENCE", stats.get("confidence", "—"))
    print("BAD_COUNT", bad_count)
    return 0 if blocking == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
