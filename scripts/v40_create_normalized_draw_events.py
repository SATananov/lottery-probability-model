from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATASET = ROOT / "data" / "historical_draws.csv"
OUTPUT_DATASET = ROOT / "data" / "v40_normalized_draw_events.csv"
REPORT_JSON = ROOT / "reports" / "v40_normalized_draw_events_report.json"
REPORT_MD = ROOT / "reports" / "v40_normalized_draw_events_report.md"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]

REQUIRED_SOURCE_COLS = [
    "draw_id",
    "date",
    *NUMBER_COLS,
    "year",
    "draw_number",
    "draw_position",
    "source_url",
]

TARGET_COLS = [
    "draw_event_id",
    "source_draw_id",
    "date",
    "year",
    "draw_number",
    "drawing_no",
    "n1",
    "n2",
    "n3",
    "n4",
    "n5",
    "n6",
    "bonus_number",
    "source_url",
    "rules_version",
    "data_status",
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def to_int_series(df: pd.DataFrame, col: str) -> pd.Series:
    values = pd.to_numeric(df[col], errors="coerce")
    if values.isna().any():
        fail(f"Column {col!r} contains non-numeric values.")
    return values.astype(int)


def validate_six_numbers(df: pd.DataFrame) -> dict[str, int]:
    number_values = df[NUMBER_COLS]

    out_of_range_rows = int(((number_values < 1) | (number_values > 49)).any(axis=1).sum())

    repeated_rows = int(
        number_values.apply(
            lambda row: len(set(row.astype(int).tolist())) != 6,
            axis=1,
        ).sum()
    )

    return {
        "out_of_range_rows": out_of_range_rows,
        "repeated_number_rows": repeated_rows,
    }


def create_normalized_events() -> dict[str, Any]:
    if not SOURCE_DATASET.exists():
        fail(f"Missing source dataset: {SOURCE_DATASET}")

    df = pd.read_csv(SOURCE_DATASET)

    missing = [col for col in REQUIRED_SOURCE_COLS if col not in df.columns]
    if missing:
        fail(f"Missing required source columns: {missing}")

    clean = df.copy()

    for col in ["draw_id", "year", "draw_number", "draw_position", *NUMBER_COLS]:
        clean[col] = to_int_series(clean, col)

    validation = validate_six_numbers(clean)
    if validation["out_of_range_rows"] or validation["repeated_number_rows"]:
        fail(
            "Source dataset failed validation: "
            f"{validation}"
        )

    normalized = pd.DataFrame()
    normalized["draw_event_id"] = clean.apply(
        lambda row: f"{int(row['year'])}-{int(row['draw_number']):03d}-{int(row['draw_position'])}",
        axis=1,
    )
    normalized["source_draw_id"] = clean["draw_id"].astype(int)
    normalized["date"] = clean["date"].astype(str)
    normalized["year"] = clean["year"].astype(int)
    normalized["draw_number"] = clean["draw_number"].astype(int)

    # v40 name:
    # drawing_no is the clearer domain name for draw_position.
    normalized["drawing_no"] = clean["draw_position"].astype(int)

    for col in NUMBER_COLS:
        normalized[col] = clean[col].astype(int)

    # Current v39 dataset has no official bonus number column.
    # Keep it blank until real source data is imported.
    normalized["bonus_number"] = ""

    normalized["source_url"] = clean["source_url"].astype(str)

    # This marks that these rows come from the stable v39 dataset.
    normalized["rules_version"] = "legacy_v39_known_draw_position"

    # Important: this does not claim complete two-drawing coverage.
    normalized["data_status"] = "known_from_v39_dataset_bonus_missing"

    normalized = normalized[TARGET_COLS]

    duplicated_event_ids = int(normalized["draw_event_id"].duplicated().sum())
    duplicated_keys = int(
        normalized.duplicated(
            subset=["year", "draw_number", "drawing_no"]
        ).sum()
    )

    if duplicated_event_ids or duplicated_keys:
        fail(
            "Normalized dataset has duplicate draw events: "
            f"duplicated_event_ids={duplicated_event_ids}, "
            f"duplicated_keys={duplicated_keys}"
        )

    OUTPUT_DATASET.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)

    normalized.to_csv(OUTPUT_DATASET, index=False, encoding="utf-8")

    drawing_counts = (
        normalized["drawing_no"]
        .value_counts()
        .sort_index()
        .astype(int)
        .to_dict()
    )

    per_year_summary = {}
    for year in sorted(normalized["year"].unique().tolist())[-15:]:
        ydf = normalized[normalized["year"] == year]
        per_year_summary[str(int(year))] = {
            "rows": int(len(ydf)),
            "drawing_no_counts": {
                str(int(k)): int(v)
                for k, v in ydf["drawing_no"]
                .value_counts()
                .sort_index()
                .to_dict()
                .items()
            },
        }

    rows_2026 = normalized[normalized["year"] == 2026]

    report = {
        "status": "PASS",
        "source_dataset": str(SOURCE_DATASET.relative_to(ROOT)),
        "output_dataset": str(OUTPUT_DATASET.relative_to(ROOT)),
        "source_rows": int(len(clean)),
        "normalized_rows": int(len(normalized)),
        "year_min": int(normalized["year"].min()),
        "year_max": int(normalized["year"].max()),
        "rows_2026": int(len(rows_2026)),
        "max_2026_draw_number": int(rows_2026["draw_number"].max()) if not rows_2026.empty else None,
        "drawing_no_counts": {str(int(k)): int(v) for k, v in drawing_counts.items()},
        "recent_year_summary": per_year_summary,
        "target_columns": TARGET_COLS,
        "validation": validation,
        "important_notes": [
            "historical_draws.csv was not modified.",
            "v40_normalized_draw_events.csv is a foundation dataset, not yet a complete official two-drawing dataset.",
            "bonus_number is intentionally blank until real bonus-number data is imported from a trusted source.",
            "Do not retrain two-drawing or bonus-number models until drawing 2 and bonus numbers are imported.",
            "Ticket checker logic should compare every ticket table against every drawing_no inside the selected draw.",
        ],
    }

    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")

    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = []
    lines.append("# v40 Normalized Draw Events Report")
    lines.append("")
    lines.append(f"Status: **{report['status']}**")
    lines.append(f"Source dataset: `{report['source_dataset']}`")
    lines.append(f"Output dataset: `{report['output_dataset']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Source rows: **{report['source_rows']}**")
    lines.append(f"- Normalized rows: **{report['normalized_rows']}**")
    lines.append(f"- Years: **{report['year_min']} - {report['year_max']}**")
    lines.append(f"- Rows in 2026: **{report['rows_2026']}**")
    lines.append(f"- Max 2026 draw number: **{report['max_2026_draw_number']}**")
    lines.append("")
    lines.append("## Drawing number counts")
    for key, value in report["drawing_no_counts"].items():
        lines.append(f"- drawing_no `{key}`: **{value}** row(s)")
    lines.append("")
    lines.append("## Recent year summary")
    for year, payload in report["recent_year_summary"].items():
        lines.append(
            f"- {year}: rows={payload['rows']}, drawing_no_counts={payload['drawing_no_counts']}"
        )
    lines.append("")
    lines.append("## Target columns")
    lines.append("```text")
    for col in report["target_columns"]:
        lines.append(col)
    lines.append("```")
    lines.append("")
    lines.append("## Important notes")
    for note in report["important_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = create_normalized_events()

    print("DONE: v40 normalized draw events dataset created.")
    print(f"SOURCE_ROWS: {report['source_rows']}")
    print(f"NORMALIZED_ROWS: {report['normalized_rows']}")
    print(f"YEARS: {report['year_min']} {report['year_max']}")
    print(f"ROWS_2026: {report['rows_2026']}")
    print(f"DRAWING_NO_COUNTS: {report['drawing_no_counts']}")
    print(f"OUTPUT_DATASET: {OUTPUT_DATASET}")
    print(f"REPORT_MD: {REPORT_MD}")


if __name__ == "__main__":
    main()
