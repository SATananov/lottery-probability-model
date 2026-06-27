from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_prize_winner_history_engine import parse_official_result_page

SAMPLE_HTML = """
<html><body>
Тото 2 - 6 от 49
Избери тираж
Тираж 49 - 2026
## Тираж 49 - 25.06.2026
Печеливши числа
* * *
5
11
44
46
47
48
Джакпот
2 189 497.94 euro
числа Брой печалби Размер на печалбата Обща сума на печалбите
6 числа 0 0.00 euro 0.00 euro
5 числа 2 11 417.30 euro 22 834.60 euro
4 числа 442 57.10 euro 25 238.20 euro
3 числа 7164 7.60 euro 54 446.40 euro
</body></html>
"""


def main() -> int:
    failures: list[str] = []
    try:
        record = parse_official_result_page(SAMPLE_HTML, "local-sample", expected_year=2026, expected_draw=49)
    except Exception as exc:
        record = {}
        failures.append(f"sample_parser_error={exc}")

    if record.get("draw_key") != "2026-49":
        failures.append("draw_key")
    if record.get("numbers_text") != "5, 11, 44, 46, 47, 48":
        failures.append("numbers_text")
    if int(record.get("winners_5") or -1) != 2:
        failures.append("winners_5")
    if int(record.get("winners_4") or -1) != 442:
        failures.append("winners_4")
    if int(record.get("winners_3") or -1) != 7164:
        failures.append("winners_3")

    print("STEP_111_3_STATUS", "PRIZE_IMPORT_SPLIT_NUMBERS_FIXED" if not failures else "CHECK_REQUIRED")
    print("BLOCKING_FAILURES", len(failures))
    print("SAMPLE_DRAW", record.get("draw_key", "—"))
    print("SAMPLE_NUMBERS", record.get("numbers_text", "—"))
    print("SAMPLE_WINNERS_5", record.get("winners_5", "—"))
    print("SAMPLE_WINNERS_4", record.get("winners_4", "—"))
    print("SAMPLE_WINNERS_3", record.get("winners_3", "—"))
    if failures:
        print("FAILURES", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
