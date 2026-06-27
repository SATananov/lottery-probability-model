from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_prize_winner_history_engine import parse_official_result_page, write_artifacts

REPORT_PATH = ROOT / "reports" / "v111_1_prize_import_parser_fix_summary.json"

SAMPLE_HTML = """
<html><body>
<h1>Тото 2 - 6 от 49</h1>
<div>Избери тираж Тираж 49 - 2026 Тираж 48 - 2026</div>
<h2>Тираж 49 - 25.06.2026</h2>
<div>Печеливши числа</div>
<div>5 11 44 46 47 48</div>
<div>Джакпот</div>
<div>2 189 497.94 euro</div>
<table>
<tr><th>числа</th><th>Брой печалби</th><th>Размер на печалбата</th><th>Обща сума на печалбите</th></tr>
<tr><td>6 числа</td><td>0</td><td>0.00 euro</td><td>0.00 euro</td></tr>
<tr><td>5 числа</td><td>2</td><td>11 417.30 euro</td><td>22 834.60 euro</td></tr>
<tr><td>4 числа</td><td>442</td><td>57.10 euro</td><td>25 238.20 euro</td></tr>
<tr><td>3 числа</td><td>7164</td><td>7.60 euro</td><td>54 446.40 euro</td></tr>
</table>
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
    record = parse_official_result_page(
        SAMPLE_HTML,
        "https://info.toto.bg/results/6x49/2026-49",
        expected_year=2026,
        expected_draw=49,
    )
    checks = []

    def add(name: str, passed: bool, details: str) -> None:
        checks.append({"check": name, "status": "OK" if passed else "FAIL", "details_bg": details})

    add("sample_draw_parsed", record.get("draw_key") == "2026-49", "Тестовият тираж се разчита коректно.")
    add("sample_numbers_parsed", record.get("numbers_text") == "5, 11, 44, 46, 47, 48", "Печелившите числа се разчитат коректно.")
    add("sample_winners_parsed", record.get("winners_5") == 2 and record.get("winners_4") == 442 and record.get("winners_3") == 7164, "Печалбите по категории се разчитат коректно.")
    add("sample_jackpot_parsed", abs(float(record.get("jackpot_eur") or 0) - 2189497.94) < 0.01, "Джакпотът се разчита коректно.")

    monitored = [
        ROOT / "src" / "v111_prize_winner_history_engine.py",
        ROOT / "src" / "v111_prize_winner_history_section.py",
        ROOT / "scripts" / "v111_1_fix_prize_import_parser.py",
    ]
    add("cyrillic_safe", not any(has_bad_text(path) for path in monitored), "Кирилицата в новите файлове е чиста.")

    base_summary = write_artifacts()
    blocking_failures = sum(1 for item in checks if item["status"] != "OK")
    status = "PRIZE_IMPORT_PARSER_FIXED" if blocking_failures == 0 else "CHECK_REQUIRED"
    report = {
        "step": "111.1",
        "name": "Prize import parser fix",
        "status": status,
        "blocking_failures": blocking_failures,
        "sample_record": record,
        "base_step_status": base_summary.get("status"),
        "imported_draws": base_summary.get("imported_draws"),
        "checks": checks,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"STEP_111_1_STATUS {status}")
    print(f"BLOCKING_FAILURES {blocking_failures}")
    print(f"SAMPLE_DRAW {record.get('draw_key')}")
    print(f"SAMPLE_NUMBERS {record.get('numbers_text')}")
    print(f"SAMPLE_WINNERS_5 {record.get('winners_5')}")
    print(f"SAMPLE_WINNERS_4 {record.get('winners_4')}")
    print(f"SAMPLE_WINNERS_3 {record.get('winners_3')}")
    return 0 if blocking_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
