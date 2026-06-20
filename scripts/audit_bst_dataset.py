from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


CSV_PATH = Path("data/historical_draws.csv")
START_YEAR = 1958
END_YEAR = 2025


def main() -> None:
    rows = list(csv.DictReader(CSV_PATH.open("r", encoding="utf-8-sig", newline="")))
    years = Counter(row["year"] for row in rows)

    full_keys = Counter(
        (
            row["year"],
            row["draw_number"],
            row.get("draw_position", ""),
            row["n1"],
            row["n2"],
            row["n3"],
            row["n4"],
            row["n5"],
            row["n6"],
        )
        for row in rows
    )

    draw_position_keys = Counter(
        (
            row["year"],
            row["draw_number"],
            row.get("draw_position", ""),
        )
        for row in rows
    )

    duplicate_full_rows = sum(1 for count in full_keys.values() if count > 1)
    duplicate_draw_position_keys = sum(1 for count in draw_position_keys.values() if count > 1)
    missing_years = [str(year) for year in range(START_YEAR, END_YEAR + 1) if str(year) not in years]

    print("BST DATASET AUDIT")
    print("-" * 40)
    print(f"Rows: {len(rows)}")
    print(f"Years: {min(years) if years else 'None'} to {max(years) if years else 'None'}")
    print(f"Missing {START_YEAR}-{END_YEAR}: {missing_years}")
    print(f"Duplicate full rows: {duplicate_full_rows}")
    print(f"Duplicate year/draw/position keys: {duplicate_draw_position_keys}")
    print("Last 20 years present:", {year: years[year] for year in sorted(years)[-20:]})

    report_path = Path("reports/data_audit_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# BST Dataset Audit",
        "",
        f"Rows: {len(rows)}",
        f"Years: {min(years) if years else 'None'} to {max(years) if years else 'None'}",
        f"Missing {START_YEAR}-{END_YEAR}: {missing_years}",
        f"Duplicate full rows: {duplicate_full_rows}",
        f"Duplicate year/draw/position keys: {duplicate_draw_position_keys}",
        "",
        "## Rows by year",
        "",
    ]

    for year in sorted(years):
        lines.append(f"- {year}: {years[year]}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
