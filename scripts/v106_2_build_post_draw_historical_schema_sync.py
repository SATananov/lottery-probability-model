from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATA_FILES = {
    "historical": ROOT / "data" / "historical_draws.csv",
    "normalized": ROOT / "data" / "v40_normalized_draw_events.csv",
    "canonical": ROOT / "data" / "v41_canonical_draw_events.csv",
}

REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v106_2"

SUMMARY_JSON = REPORTS_DIR / "v106_2_post_draw_historical_schema_sync_summary.json"
SUMMARY_MD = REPORTS_DIR / "v106_2_post_draw_historical_schema_sync_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v106_2_post_draw_historical_schema_sync_checklist.csv"
MODEL_JSON = MODELS_DIR / "v106_2_post_draw_historical_schema_sync_model.json"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def safe_int(value, default=None):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def pick(row: dict[str, str], names: list[str], default=""):
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def extract_numbers(row: dict[str, str]) -> list[int]:
    possible_sets = [
        ["n1", "n2", "n3", "n4", "n5", "n6"],
        ["num1", "num2", "num3", "num4", "num5", "num6"],
        ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
        ["ball1", "ball2", "ball3", "ball4", "ball5", "ball6"],
        ["number1", "number2", "number3", "number4", "number5", "number6"],
    ]

    for columns in possible_sets:
        values = [safe_int(row.get(col)) for col in columns]
        if all(value is not None for value in values):
            return sorted(int(value) for value in values)

    numbers_text = pick(row, ["numbers", "draw_numbers", "combination"], "")
    if numbers_text:
        cleaned = (
            numbers_text.replace("[", "")
            .replace("]", "")
            .replace(";", ",")
            .replace("|", ",")
            .replace(" ", ",")
        )
        values = [safe_int(part) for part in cleaned.split(",") if part.strip()]
        values = [int(value) for value in values if value is not None]
        if len(values) >= 6:
            return sorted(values[:6])

    return []


def latest_historical_draw(rows: list[dict[str, str]]) -> dict:
    if not rows:
        return {
            "date": None,
            "draw_no": None,
            "numbers": [],
        }

    def sort_key(row: dict[str, str]):
        date = pick(row, ["date", "draw_date"], "")
        year = safe_int(pick(row, ["year"], ""), 0) or 0
        draw_no = safe_int(pick(row, ["draw_number", "draw_no", "draw_id", "drawing_no"], ""), 0) or 0
        return (date, year, draw_no)

    row = max(rows, key=sort_key)
    return {
        "date": pick(row, ["date", "draw_date"], None),
        "draw_no": pick(row, ["draw_number", "draw_no", "draw_id", "drawing_no"], None),
        "numbers": extract_numbers(row),
    }


def build_step() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    rows_by_name = {name: read_csv_rows(path) for name, path in DATA_FILES.items()}
    row_counts = {name: len(rows) for name, rows in rows_by_name.items()}
    latest = latest_historical_draw(rows_by_name["historical"])

    checklist = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes"):
        checklist.append(
            {
                "check": name,
                "status": "OK" if passed else "FAIL",
                "blocking": blocking,
                "details_bg": details_bg,
            }
        )

    all_files_exist = all(path.exists() for path in DATA_FILES.values())
    counts_match = len(set(row_counts.values())) == 1 and row_counts["historical"] > 0
    latest_has_six_numbers = len(latest["numbers"]) == 6
    latest_numbers_valid = (
        latest_has_six_numbers
        and all(1 <= number <= 49 for number in latest["numbers"])
        and len(set(latest["numbers"])) == 6
    )

    add_check(
        "dataset_files_exist",
        all_files_exist,
        ", ".join(f"{name}={path.exists()}" for name, path in DATA_FILES.items()),
    )
    add_check(
        "post_draw_row_counts_synced",
        counts_match,
        f"historical={row_counts['historical']}, normalized={row_counts['normalized']}, canonical={row_counts['canonical']}",
    )
    add_check(
        "latest_draw_has_six_numbers",
        latest_has_six_numbers,
        f"latest_draw={latest}",
    )
    add_check(
        "latest_draw_numbers_valid",
        latest_numbers_valid,
        f"numbers={latest['numbers']}",
    )

    blocking_failures = sum(
        1 for row in checklist if row["blocking"] == "yes" and row["status"] != "OK"
    )

    status = "POST_DRAW_DATASETS_SYNCED" if blocking_failures == 0 else "CHECK_REQUIRED"

    summary = {
        "step": "106.2",
        "name": "Post-draw Historical Schema Sync",
        "status": status,
        "blocking_failures": blocking_failures,
        "dataset_rows": row_counts["historical"],
        "row_counts": row_counts,
        "latest_draw": latest,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checklist": checklist,
        "notes_bg": [
            "????????? ???? ????? ?????????? ?????? ????? ? ????????????? ????? historical, normalized ? canonical datasets.",
            "???? builder ? ???????? verifier ? ?? ?????? ?? ???????? apply helper ???????.",
        ],
    }

    SUMMARY_JSON.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    MODEL_JSON.write_text(
        json.dumps(
            {
                "step": summary["step"],
                "status": summary["status"],
                "dataset_rows": summary["dataset_rows"],
                "row_counts": summary["row_counts"],
                "latest_draw": summary["latest_draw"],
                "blocking_failures": summary["blocking_failures"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Step 106.2 ? Post-draw Historical Schema Sync",
        "",
        f"- Status: `{summary['status']}`",
        f"- Blocking failures: `{summary['blocking_failures']}`",
        f"- Dataset rows: `{summary['dataset_rows']}`",
        f"- Row counts: `{summary['row_counts']}`",
        f"- Latest draw: `{summary['latest_draw']}`",
        "",
        "## Checklist",
        "",
    ]

    for item in checklist:
        md_lines.append(
            f"- `{item['status']}` ? {item['check']}: {item['details_bg']}"
        )

    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"STEP_106_2_STATUS {summary['status']}")
    print(f"BLOCKING_FAILURES {summary['blocking_failures']}")
    print(f"DATASET_ROWS {summary['dataset_rows']}")
    print(f"ROW_COUNTS {summary['row_counts']}")
    print(f"LATEST_DRAW {latest['date']} {latest['numbers']}")

    return summary


if __name__ == "__main__":
    build_step()
