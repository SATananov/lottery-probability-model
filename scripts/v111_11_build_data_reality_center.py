from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "reports" / "v111_11_data_reality_center_report.json"
REPORT_MD = ROOT / "reports" / "v111_11_data_reality_center_report.md"
MODEL_DIR = ROOT / "models" / "v111_11"
MODEL_JSON = MODEL_DIR / "data_reality_center_status.json"
DRAW_PATH = ROOT / "data" / "historical_draws.csv"
PRIZE_PATH = ROOT / "data" / "prize_winner_history.csv"
DB_PATH = ROOT / "data" / "user_journal.db"
SECTION_PATH = ROOT / "src" / "v111_11_data_reality_center_section.py"
APP_PATH = ROOT / "streamlit_app.py"


def _safe_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(pd.read_csv(path, encoding="utf-8-sig"))
    except Exception:
        try:
            return len(pd.read_csv(path))
        except Exception:
            return 0


def _ticket_count() -> tuple[int, int]:
    if not DB_PATH.exists():
        return 0, 0
    try:
        with sqlite3.connect(DB_PATH) as conn:
            tickets = conn.execute("SELECT COUNT(*) FROM played_tickets").fetchone()[0]
            results = conn.execute("SELECT COUNT(*) FROM played_ticket_results").fetchone()[0]
            return int(tickets), int(results)
    except Exception:
        return 0, 0


def _bad_text_count(paths: list[Path]) -> int:
    bad = 0
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        bad += text.count("?" * 4) + text.count(chr(0xFFFD))
    return bad


def main() -> None:
    failures: list[str] = []
    draw_rows = _safe_csv_rows(DRAW_PATH)
    prize_rows = _safe_csv_rows(PRIZE_PATH)
    tickets, results = _ticket_count()

    if not SECTION_PATH.exists():
        failures.append("Липсва секцията Матрица на данните")
    if not APP_PATH.exists():
        failures.append("Липсва streamlit_app.py")
    else:
        app_text = APP_PATH.read_text(encoding="utf-8", errors="replace")
        if "render_v111_11_data_reality_center_page" not in app_text:
            failures.append("streamlit_app.py не е свързан с новата страница")
        if "Матрица на данните" not in app_text:
            failures.append("Новата страница не е добавена в менюто")
    if draw_rows <= 0:
        failures.append("Липсва история на изтеглените числа")

    bad_count = _bad_text_count([SECTION_PATH, ROOT / "scripts" / "v111_11_build_data_reality_center.py"])
    if bad_count:
        failures.append(f"Открита е счупена кирилица/маркер: {bad_count}")

    status = "DATA_REALITY_CENTER_READY" if not failures else "DATA_REALITY_CENTER_NEEDS_ATTENTION"
    summary = {
        "step": "111.11",
        "status": status,
        "blocking_failures": len(failures),
        "failures": failures,
        "historical_draw_rows": draw_rows,
        "prize_history_rows": prize_rows,
        "played_tickets": tickets,
        "evaluated_ticket_results": results,
        "bad_count": bad_count,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(
        "# Step 111.11 Data Reality Center\n\n"
        f"Status: {status}\n\n"
        f"Blocking failures: {len(failures)}\n\n"
        f"Historical draw rows: {draw_rows}\n\n"
        f"Prize history rows: {prize_rows}\n\n"
        f"Played tickets: {tickets}\n\n"
        f"Evaluated ticket results: {results}\n\n"
        f"Bad count: {bad_count}\n",
        encoding="utf-8",
    )
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"STEP_111_11_STATUS {status}")
    print(f"BLOCKING_FAILURES {len(failures)}")
    print(f"HISTORICAL_DRAW_ROWS {draw_rows}")
    print(f"PRIZE_HISTORY_ROWS {prize_rows}")
    print(f"PLAYED_TICKETS {tickets}")
    print(f"EVALUATED_RESULTS {results}")
    print(f"BAD_COUNT {bad_count}")
    for failure in failures:
        print("FAILURE", failure)


if __name__ == "__main__":
    main()
