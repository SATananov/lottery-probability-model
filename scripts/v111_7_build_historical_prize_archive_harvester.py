from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_7_historical_prize_archive_harvester import build_self_check

REPORT_PATH = ROOT / "reports" / "v111_7_historical_prize_archive_harvester_report.json"


def _bad_text_scan() -> list[str]:
    bad: list[str] = []
    targets = [
        ROOT / "src" / "v111_7_historical_prize_archive_harvester.py",
        ROOT / "src" / "v111_7_historical_prize_archive_section.py",
        ROOT / "scripts" / "v111_7_build_historical_prize_archive_harvester.py",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8", errors="replace")
        if ("?" * 4) in text or chr(0xFFFD) in text:
            bad.append(str(path.relative_to(ROOT)))
    return bad


def main() -> int:
    result = build_self_check()
    bad = _bad_text_scan()
    blocking = list(result.get("blocking_failures") or [])
    blocking.extend([f"bad_text:{item}" for item in bad])
    status = "HISTORICAL_PRIZE_ARCHIVE_HARVESTER_READY" if not blocking else "HISTORICAL_PRIZE_ARCHIVE_HARVESTER_CHECK_FAILED"
    payload = {
        "step": "111.7",
        "status": status,
        "blocking_failures": blocking,
        "blocking_failure_count": len(blocking),
        "self_check": result,
        "bad_text_files": bad,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("STEP_111_7_STATUS", status)
    print("BLOCKING_FAILURES", len(blocking))
    print("SAMPLE_NUMBERS", result.get("sample_record", {}).get("numbers_text"))
    print("SAMPLE_WINNERS_5", result.get("sample_record", {}).get("winners_5"))
    print("SAMPLE_VERIFIED_BY_NUMBERS", result.get("sample_quality", {}).get("verified_by_numbers"))
    print("BAD_COUNT", len(bad))
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
