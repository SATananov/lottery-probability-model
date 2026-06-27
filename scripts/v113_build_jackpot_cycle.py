from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BAD_MARKERS = ["?" * 4, chr(0xFFFD)]


def main() -> int:
    from src.v113_jackpot_cycle_section import write_jackpot_cycle_reports

    stats = write_jackpot_cycle_reports()
    blocking = int(stats.get("blocking_failures", 0) or 0)
    bad_count = 0
    checked_files = [
        ROOT / "src" / "v113_jackpot_cycle_section.py",
        ROOT / "scripts" / "v113_build_jackpot_cycle.py",
        ROOT / "reports" / "v113_jackpot_cycle_report.json",
        ROOT / "reports" / "v113_jackpot_cycle_report.md",
    ]
    for path in checked_files:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            bad_count += sum(text.count(marker) for marker in BAD_MARKERS)
    if bad_count:
        blocking += 1
    print("STEP_113_STATUS", stats.get("status", "UNKNOWN"))
    print("BLOCKING_FAILURES", blocking)
    print("PRIZE_HISTORY_ROWS", stats.get("rows", 0))
    print("ANALYSIS_ROWS", stats.get("analysis_rows", 0))
    print("SIX_EVENTS", stats.get("six_event_count", 0))
    print("GAP_AFTER_LAST_SIX", stats.get("gap_after_last_six"))
    print("JACKPOT_GROWTH_EUR", stats.get("jackpot_growth_eur", 0))
    print("BAD_COUNT", bad_count)
    return 0 if blocking == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
