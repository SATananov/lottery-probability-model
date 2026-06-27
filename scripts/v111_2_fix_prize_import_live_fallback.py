from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_prize_winner_history_engine import parse_official_result_page, write_artifacts

REPORT_PATH = ROOT / "reports" / "v111_2_prize_import_live_fallback_summary.json"

SAMPLE_WITH_TITLE = """
<html><body>
<h2>Тираж 49 - 25.06.2026</h2>
<div>Печеливши числа</div>
<div>5 11 44 46 47 48</div>
<div>Джакпот</div>
<div>2 189 497.94 euro</div>
<table>
<tr><td>6 числа</td><td>0</td><td>0.00 euro</td><td>0.00 euro</td></tr>
<tr><td>5 числа</td><td>2</td><td>11 417.30 euro</td><td>22 834.60 euro</td></tr>
<tr><td>4 числа</td><td>442</td><td>57.10 euro</td><td>25 238.20 euro</td></tr>
<tr><td>3 числа</td><td>7164</td><td>7.60 euro</td><td>54 446.40 euro</td></tr>
</table>
</body></html>
"""

SAMPLE_WITHOUT_TITLE = """
<html><body>
<h1>Тото 2 - 6 от 49</h1>
<div>Избери тираж Тираж 49 - 2026 Тираж 48 - 2026</div>
<div>Печеливши числа</div>
<div>5 11 44 46 47 48</div>
<div>Джакпот</div>
<div>2 189 497.94 euro</div>
<div>6 числа 0 0.00 euro 0.00 euro</div>
<div>5 числа 2 11 417.30 euro 22 834.60 euro</div>
<div>4 числа 442 57.10 euro 25 238.20 euro</div>
<div>3 числа 7164 7.60 euro 54 446.40 euro</div>
</body></html>
"""


def has_bad_text(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return True
    markers = ["?" * 4, chr(0xFFFD), chr(92) + "ufffd"]
    return any(marker in text for marker in markers)


def main() -> int:
    checks = []

    def add(name: str, passed: bool, details: str) -> None:
        checks.append({"check": name, "status": "OK" if passed else "FAIL", "details_bg": details})

    record_a = parse_official_result_page(
        SAMPLE_WITH_TITLE,
        "https://info.toto.bg/results/6x49/2026-49",
        expected_year=2026,
        expected_draw=49,
    )
    record_b = parse_official_result_page(
        SAMPLE_WITHOUT_TITLE,
        "https://info.toto.bg/results/6x49/2026-49",
        expected_year=2026,
        expected_draw=49,
    )

    add("title_page_parsed", record_a.get("draw_key") == "2026-49", "Страница със заглавие се разчита коректно.")
    add("fallback_page_parsed", record_b.get("draw_key") == "2026-49", "Страница без подробно заглавие се разчита чрез fallback режим.")
    add("fallback_numbers", record_b.get("numbers_text") == "5, 11, 44, 46, 47, 48", "Fallback режимът разчита шестте числа.")
    add("fallback_winners", record_b.get("winners_5") == 2 and record_b.get("winners_4") == 442 and record_b.get("winners_3") == 7164, "Fallback режимът разчита печалбите по категории.")

    monitored = [
        ROOT / "src" / "v111_prize_winner_history_engine.py",
        ROOT / "src" / "v111_prize_winner_history_section.py",
        ROOT / "scripts" / "v111_2_fix_prize_import_live_fallback.py",
    ]
    add("cyrillic_safe", not any(has_bad_text(path) for path in monitored), "Кирилицата в новите файлове е чиста.")

    base_summary = write_artifacts()
    blocking_failures = sum(1 for item in checks if item["status"] != "OK")
    status = "PRIZE_IMPORT_LIVE_FALLBACK_READY" if blocking_failures == 0 else "CHECK_REQUIRED"
    report = {
        "step": "111.2",
        "name": "Prize import live fallback parser",
        "status": status,
        "blocking_failures": blocking_failures,
        "sample_record": record_b,
        "base_step_status": base_summary.get("status"),
        "imported_draws": base_summary.get("imported_draws"),
        "checks": checks,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"STEP_111_2_STATUS {status}")
    print(f"BLOCKING_FAILURES {blocking_failures}")
    print(f"SAMPLE_DRAW {record_b.get('draw_key')}")
    print(f"SAMPLE_NUMBERS {record_b.get('numbers_text')}")
    print(f"SAMPLE_WINNERS_5 {record_b.get('winners_5')}")
    print(f"SAMPLE_WINNERS_4 {record_b.get('winners_4')}")
    print(f"SAMPLE_WINNERS_3 {record_b.get('winners_3')}")
    return 0 if blocking_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
