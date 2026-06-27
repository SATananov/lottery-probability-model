from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_prize_winner_history_engine import parse_official_result_page, _parse_prize_rows_from_text

REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

SAMPLE_NORMAL = """
Тото 2 - 6 от 49 Избери тираж Тираж 49 - 2026
Тираж 49 - 25.06.2026
Печеливши числа
5 11 44 46 47 48
Джакпот
2 189 497.94 euro
числа Брой печалби Размер на печалбата Обща сума на печалбите
6 числа 0 0.00 euro 0.00 euro
5 числа 2 11 417.30 euro 22 834.60 euro
4 числа 442 57.10 euro 25 238.20 euro
3 числа 7164 7.60 euro 54 446.40 euro
Тото 2 5 от 35
"""

SAMPLE_SPLIT = """
Тото 2 - 6 от 49
Избери тираж
Тираж 49 - 2026
Тираж 49 - 25.06.2026
Печеливши числа
*
*
*
5
11
44
46
47
48
Джакпот
2 189 497.94
euro
числа
Брой печалби
Размер на печалбата
Обща сума на печалбите
6
числа
0
0.00
euro
0.00
euro
5
числа
2
11 417.30
euro
22 834.60
euro
4
числа
442
57.10
euro
25 238.20
euro
3
числа
7164
7.60
euro
54 446.40
euro
"""

normal_record = parse_official_result_page(SAMPLE_NORMAL, "sample://normal", expected_year=2026, expected_draw=49)
split_record = parse_official_result_page(SAMPLE_SPLIT, "sample://split", expected_year=2026, expected_draw=49)
rows = _parse_prize_rows_from_text(SAMPLE_SPLIT)

failures: list[str] = []
for name, record in [("normal", normal_record), ("split", split_record)]:
    if record.get("numbers_text") != "5, 11, 44, 46, 47, 48":
        failures.append(f"{name}: numbers parse failed")
    if record.get("winners_5") != 2:
        failures.append(f"{name}: winners_5 parse failed")
    if record.get("winners_4") != 442:
        failures.append(f"{name}: winners_4 parse failed")
    if record.get("winners_3") != 7164:
        failures.append(f"{name}: winners_3 parse failed")

if sorted(rows.keys()) != [3, 4, 5, 6]:
    failures.append("split: prize rows 6/5/4/3 not all parsed")

bad_markers = []
for rel in ["src/v111_prize_winner_history_engine.py", "scripts/v111_5_fix_prize_import_table_parser.py"]:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8", errors="replace")
    if ("?" * 4) in text or chr(0xFFFD) in text:
        bad_markers.append(rel)

summary = {
    "step": "111.5",
    "status": "PRIZE_IMPORT_TABLE_PARSER_FIXED" if not failures and not bad_markers else "CHECK_REQUIRED",
    "blocking_failures": len(failures) + len(bad_markers),
    "sample_draw": "2026-49",
    "sample_numbers": normal_record.get("numbers_text"),
    "sample_winners_5": normal_record.get("winners_5"),
    "sample_winners_4": normal_record.get("winners_4"),
    "sample_winners_3": normal_record.get("winners_3"),
    "parsed_categories": sorted(rows.keys()),
    "bad_cyrillic_files": bad_markers,
    "failures": failures,
}
(REPORTS / "v111_5_prize_import_table_parser_fix.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"STEP_111_5_STATUS {summary['status']}")
print(f"BLOCKING_FAILURES {summary['blocking_failures']}")
print(f"SAMPLE_DRAW {summary['sample_draw']}")
print(f"SAMPLE_NUMBERS {summary['sample_numbers']}")
print(f"SAMPLE_WINNERS_5 {summary['sample_winners_5']}")
print(f"SAMPLE_WINNERS_4 {summary['sample_winners_4']}")
print(f"SAMPLE_WINNERS_3 {summary['sample_winners_3']}")
if failures or bad_markers:
    raise SystemExit(1)
