from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v111_prize_winner_history_engine import parse_official_result_page
REPORTS_DIR = ROOT / "reports"
REPORT_PATH = REPORTS_DIR / "v111_4_prize_import_local_numbers_fallback.json"


def main() -> int:
    # Synthetic БСТ-like page with the prize table present, but without visible number balls.
    # The parser must use local synchronized draw numbers and keep prize data from the page.
    sample_html = """
    <html><body>
      <main>
        <h1>Тираж 49 - 25.06.2026</h1>
        <section>Печеливши числа</section>
        <section>Джакпот 2 189 497.94 euro</section>
        <table>
          <tr><td>6 числа</td><td>0</td><td>0.00 euro</td><td>0.00 euro</td></tr>
          <tr><td>5 числа</td><td>2</td><td>7 640.24 euro</td><td>15 280.48 euro</td></tr>
          <tr><td>4 числа</td><td>442</td><td>34.57 euro</td><td>15 277.94 euro</td></tr>
          <tr><td>3 числа</td><td>7164</td><td>2.00 euro</td><td>14 328.00 euro</td></tr>
        </table>
      </main>
    </body></html>
    """
    failures: list[str] = []
    try:
        record = parse_official_result_page(
            sample_html,
            "https://info.toto.bg/results/6x49/2026-49",
            expected_year=2026,
            expected_draw=49,
        )
    except Exception as exc:
        failures.append(f"Parser fallback failed: {exc}")
        record = {}

    expected_numbers = [5, 11, 44, 46, 47, 48]
    numbers = [int(record.get(f"n{pos}", -1)) for pos in range(1, 7)] if record else []
    if numbers != expected_numbers:
        failures.append(f"Expected local fallback numbers {expected_numbers}, got {numbers}")
    if int(record.get("winners_5", -1)) != 2:
        failures.append("Expected winners_5 to be 2")
    if int(record.get("winners_4", -1)) != 442:
        failures.append("Expected winners_4 to be 442")
    if int(record.get("winners_3", -1)) != 7164:
        failures.append("Expected winners_3 to be 7164")
    if "локалния синхронизиран архив" not in str(record.get("note", "")):
        failures.append("Expected note to mention local synchronized archive fallback")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "step": "111.4",
        "status": "PRIZE_IMPORT_LOCAL_NUMBERS_FALLBACK_READY" if not failures else "CHECK_REQUIRED",
        "blocking_failures": len(failures),
        "sample_draw": "2026-49",
        "sample_numbers": numbers,
        "sample_winners_5": record.get("winners_5") if record else None,
        "sample_winners_4": record.get("winners_4") if record else None,
        "sample_winners_3": record.get("winners_3") if record else None,
        "failures": failures,
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("STEP_111_4_STATUS", payload["status"])
    print("BLOCKING_FAILURES", payload["blocking_failures"])
    print("SAMPLE_DRAW", payload["sample_draw"])
    print("SAMPLE_NUMBERS", ", ".join(str(item) for item in numbers))
    print("SAMPLE_WINNERS_5", payload["sample_winners_5"])
    print("SAMPLE_WINNERS_4", payload["sample_winners_4"])
    print("SAMPLE_WINNERS_3", payload["sample_winners_3"])
    if failures:
        for failure in failures:
            print("FAIL", failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
