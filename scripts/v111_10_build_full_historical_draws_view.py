from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "historical_draws.csv"
REPORT_JSON = ROOT / "reports" / "v111_10_full_historical_draws_view_report.json"
REPORT_MD = ROOT / "reports" / "v111_10_full_historical_draws_view_report.md"
MODEL_DIR = ROOT / "models" / "v111_10"
MODEL_JSON = MODEL_DIR / "full_historical_draws_view_status.json"


def main() -> None:
    failures: list[str] = []
    rows = 0
    first_year = None
    last_year = None
    bad_count = 0

    if not DATA_PATH.exists():
        failures.append("Липсва data/historical_draws.csv")
    else:
        df = pd.read_csv(DATA_PATH)
        rows = len(df)
        if rows <= 0:
            failures.append("Историята на изтеглените числа е празна")
        required = ["year", "draw_number", "n1", "n2", "n3", "n4", "n5", "n6"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            failures.append("Липсващи колони: " + ", ".join(missing))
        if "year" in df.columns and rows:
            years = pd.to_numeric(df["year"], errors="coerce").dropna()
            if not years.empty:
                first_year = int(years.min())
                last_year = int(years.max())
        for col in ["n1", "n2", "n3", "n4", "n5", "n6"]:
            if col in df.columns:
                nums = pd.to_numeric(df[col], errors="coerce")
                bad_count += int(((nums < 1) | (nums > 49) | nums.isna()).sum())
        if bad_count:
            failures.append(f"Има невалидни числа извън 1–49: {bad_count}")

    section_path = ROOT / "src" / "v111_10_full_historical_draws_section.py"
    app_path = ROOT / "streamlit_app.py"
    if not section_path.exists():
        failures.append("Липсва новата секция за пълна история")
    if not app_path.exists() or "render_full_historical_draws_section" not in app_path.read_text(encoding="utf-8", errors="replace"):
        failures.append("streamlit_app.py не е свързан с новата секция")

    status = "FULL_HISTORICAL_DRAWS_VIEW_READY" if not failures else "FULL_HISTORICAL_DRAWS_VIEW_NEEDS_ATTENTION"
    summary = {
        "step": "111.10",
        "status": status,
        "blocking_failures": len(failures),
        "failures": failures,
        "historical_draw_rows": rows,
        "first_year": first_year,
        "last_year": last_year,
        "bad_count": bad_count,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(
        "# Step 111.10 Full Historical Draws View\n\n"
        f"Status: {status}\n\n"
        f"Blocking failures: {len(failures)}\n\n"
        f"Historical draw rows: {rows}\n\n"
        f"Years: {first_year}–{last_year}\n\n"
        f"Bad count: {bad_count}\n",
        encoding="utf-8",
    )
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"STEP_111_10_STATUS {status}")
    print(f"BLOCKING_FAILURES {len(failures)}")
    print(f"HISTORICAL_DRAW_ROWS {rows}")
    print(f"YEARS {first_year}-{last_year}")
    print(f"BAD_COUNT {bad_count}")
    if failures:
        for failure in failures:
            print("FAILURE", failure)


if __name__ == "__main__":
    main()
