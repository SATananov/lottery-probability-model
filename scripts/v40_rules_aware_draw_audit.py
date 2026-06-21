from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "historical_draws.csv"
REPORTS_DIR = ROOT / "reports"
JSON_REPORT = REPORTS_DIR / "v40_rules_aware_draw_audit.json"
MD_REPORT = REPORTS_DIR / "v40_rules_aware_draw_audit.md"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]

REQUIRED_COLS = [
    "draw_id",
    "date",
    *NUMBER_COLS,
    "year",
    "draw_number",
    "draw_position",
    "source_url",
]

TARGET_SCHEMA = [
    "draw_id",
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
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def as_int_series(series: pd.Series, col_name: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.isna().any():
        bad_count = int(values.isna().sum())
        fail(f"Column {col_name!r} contains {bad_count} non-numeric value(s).")
    return values.astype(int)


def inspect_dataset(df: pd.DataFrame) -> dict[str, Any]:
    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    extra_cols = [col for col in df.columns if col not in REQUIRED_COLS]

    if missing_cols:
        fail(f"Missing required column(s): {missing_cols}")

    cleaned = df.copy()

    for col in ["draw_id", "year", "draw_number", "draw_position", *NUMBER_COLS]:
        cleaned[col] = as_int_series(cleaned[col], col)

    row_count = int(len(cleaned))

    duplicate_draw_ids = int(cleaned["draw_id"].duplicated().sum())

    duplicate_keys = int(
        cleaned.duplicated(
            subset=["year", "draw_number", "draw_position"]
        ).sum()
    )

    number_values = cleaned[NUMBER_COLS]

    out_of_range_mask = (number_values < 1) | (number_values > 49)
    out_of_range_rows = int(out_of_range_mask.any(axis=1).sum())

    repeated_numbers_rows = int(
        number_values.apply(
            lambda row: len(set(row.tolist())) != 6,
            axis=1,
        ).sum()
    )

    draw_position_counts = (
        cleaned["draw_position"]
        .value_counts(dropna=False)
        .sort_index()
        .astype(int)
        .to_dict()
    )

    per_year_position_counts = (
        cleaned.groupby(["year", "draw_position"])
        .size()
        .unstack(fill_value=0)
        .astype(int)
    )

    recent_years = sorted(cleaned["year"].unique().tolist())[-15:]
    recent_year_position_summary = {}

    for year in recent_years:
        year_rows = cleaned[cleaned["year"] == year]
        recent_year_position_summary[str(int(year))] = {
            "rows": int(len(year_rows)),
            "positions": {
                str(int(k)): int(v)
                for k, v in year_rows["draw_position"]
                .value_counts()
                .sort_index()
                .to_dict()
                .items()
            },
        }

    years_with_only_position_1 = []
    years_with_multiple_positions = []

    for year, row in per_year_position_counts.iterrows():
        active_positions = [
            int(pos)
            for pos, count in row.items()
            if int(count) > 0
        ]

        if active_positions == [1]:
            years_with_only_position_1.append(int(year))
        elif len(active_positions) > 1:
            years_with_multiple_positions.append(int(year))

    current_schema_support = {
        "has_draw_position": "draw_position" in cleaned.columns,
        "has_drawing_no": "drawing_no" in cleaned.columns,
        "has_bonus_number": "bonus_number" in cleaned.columns,
        "has_rules_version": "rules_version" in cleaned.columns,
    }

    rows_2026 = cleaned[cleaned["year"] == 2026]

    date_series = pd.to_datetime(cleaned["date"], errors="coerce")
    valid_dates = date_series.dropna()
    last_valid_date = (
        valid_dates.max().strftime("%Y-%m-%d")
        if not valid_dates.empty
        else None
    )

    audit_status = "PASS"
    warnings = []

    if duplicate_draw_ids:
        audit_status = "WARN"
        warnings.append(f"Duplicate draw_id values: {duplicate_draw_ids}")

    if duplicate_keys:
        audit_status = "WARN"
        warnings.append(
            f"Duplicate year/draw_number/draw_position keys: {duplicate_keys}"
        )

    if out_of_range_rows:
        audit_status = "WARN"
        warnings.append(f"Rows with number outside 1..49: {out_of_range_rows}")

    if repeated_numbers_rows:
        audit_status = "WARN"
        warnings.append(
            f"Rows with repeated numbers inside one 6-number draw: {repeated_numbers_rows}"
        )

    if not current_schema_support["has_bonus_number"]:
        warnings.append("Dataset has no bonus_number column yet.")

    if not current_schema_support["has_rules_version"]:
        warnings.append("Dataset has no rules_version column yet.")

    if not current_schema_support["has_drawing_no"]:
        warnings.append(
            "Dataset uses draw_position, but not the clearer v40 name drawing_no yet."
        )

    if not rows_2026.empty:
        pos_2026 = (
            rows_2026["draw_position"]
            .value_counts()
            .sort_index()
            .astype(int)
            .to_dict()
        )

        if pos_2026 == {1: len(rows_2026)}:
            warnings.append(
                "2026 currently contains only draw_position=1. If 2026 has two official drawings per draw, second-drawing data still needs to be imported separately."
            )

    return {
        "audit_name": "v40_rules_aware_draw_audit",
        "audit_status": audit_status,
        "dataset_path": str(DATASET_PATH.relative_to(ROOT)),
        "row_count": row_count,
        "columns": list(cleaned.columns),
        "missing_required_columns": missing_cols,
        "extra_columns": extra_cols,
        "target_schema_for_v40": TARGET_SCHEMA,
        "year_min": int(cleaned["year"].min()),
        "year_max": int(cleaned["year"].max()),
        "last_valid_date": last_valid_date,
        "rows_2026": int(len(rows_2026)),
        "max_2026_draw_number": (
            int(rows_2026["draw_number"].max())
            if not rows_2026.empty
            else None
        ),
        "draw_position_counts": {
            str(k): int(v)
            for k, v in draw_position_counts.items()
        },
        "recent_year_position_summary": recent_year_position_summary,
        "years_with_only_draw_position_1": years_with_only_position_1,
        "years_with_multiple_draw_positions": years_with_multiple_positions,
        "current_schema_support": current_schema_support,
        "duplicate_draw_ids": duplicate_draw_ids,
        "duplicate_year_draw_position_keys": duplicate_keys,
        "out_of_range_rows": out_of_range_rows,
        "repeated_numbers_rows": repeated_numbers_rows,
        "warnings": warnings,
        "recommendation": [
            "Keep the existing v39 dataset as the stable baseline.",
            "Do not retrain new two-drawing models until second-drawing and bonus-number data are imported.",
            "For v40, create a normalized draw-event dataset with drawing_no and bonus_number instead of overwriting historical_draws.csv directly.",
            "After the normalized dataset is created, train separate models for drawing 1, drawing 2, combined analysis, and bonus number analysis.",
        ],
    }


def write_markdown(report: dict[str, Any]) -> str:
    lines = []

    lines.append("# v40 Rules-aware Draw Audit")
    lines.append("")
    lines.append(f"Status: **{report['audit_status']}**")
    lines.append(f"Dataset: `{report['dataset_path']}`")
    lines.append(f"Rows: **{report['row_count']}**")
    lines.append(f"Years: **{report['year_min']} - {report['year_max']}**")
    lines.append(f"Rows in 2026: **{report['rows_2026']}**")
    lines.append(f"Last valid date: **{report['last_valid_date']}**")
    lines.append("")

    lines.append("## Current schema support")
    for key, value in report["current_schema_support"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")

    lines.append("## Draw position counts")
    for key, value in report["draw_position_counts"].items():
        lines.append(f"- draw_position `{key}`: **{value}** row(s)")
    lines.append("")

    lines.append("## Recent year position summary")
    for year, payload in report["recent_year_position_summary"].items():
        lines.append(
            f"- {year}: rows={payload['rows']}, positions={payload['positions']}"
        )
    lines.append("")

    lines.append("## Validation checks")
    lines.append(f"- Duplicate draw_id values: **{report['duplicate_draw_ids']}**")
    lines.append(
        f"- Duplicate year/draw_number/draw_position keys: **{report['duplicate_year_draw_position_keys']}**"
    )
    lines.append(f"- Rows with numbers outside 1..49: **{report['out_of_range_rows']}**")
    lines.append(
        f"- Rows with repeated numbers inside a draw: **{report['repeated_numbers_rows']}**"
    )
    lines.append("")

    if report["warnings"]:
        lines.append("## Warnings / next-step notes")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## Recommended v40 target schema")
    lines.append("```text")
    for col in report["target_schema_for_v40"]:
        lines.append(col)
    lines.append("```")
    lines.append("")

    lines.append("## Recommendation")
    for item in report["recommendation"]:
        lines.append(f"- {item}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    if not DATASET_PATH.exists():
        fail(f"Dataset not found: {DATASET_PATH}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET_PATH)
    report = inspect_dataset(df)

    JSON_REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    MD_REPORT.write_text(
        write_markdown(report),
        encoding="utf-8",
    )

    print("DONE: v40 rules-aware draw audit completed.")
    print(f"STATUS: {report['audit_status']}")
    print(f"ROWS: {report['row_count']}")
    print(f"YEARS: {report['year_min']} {report['year_max']}")
    print(f"ROWS_2026: {report['rows_2026']}")
    print(f"DRAW_POSITION_COUNTS: {report['draw_position_counts']}")
    print(f"REPORT_JSON: {JSON_REPORT}")
    print(f"REPORT_MD: {MD_REPORT}")

    if report["warnings"]:
        print("WARNINGS:")
        for warning in report["warnings"]:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
