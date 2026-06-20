import csv
from collections import Counter, defaultdict
from pathlib import Path

csv_path = Path("data/historical_draws.csv")

rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))

print("DATA AUDIT")
print("-" * 40)
print("Rows:", len(rows))

years = Counter(row["year"] for row in rows)
print("Year range:", min(years) if years else "None", "to", max(years) if years else "None")
print("Missing 1958-2025:", [str(y) for y in range(1958, 2026) if str(y) not in years])

print()
print("Rows by year:")
for year in sorted(years):
    print(year, years[year])

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

duplicate_full_rows = [key for key, count in full_keys.items() if count > 1]

draw_keys = Counter(
    (
        row["year"],
        row["draw_number"],
        row.get("draw_position", ""),
    )
    for row in rows
)

duplicate_draw_keys = [key for key, count in draw_keys.items() if count > 1]

print()
print("Unique full rows:", len(full_keys))
print("Duplicate full rows:", len(duplicate_full_rows))
print("Duplicate year/draw/position keys:", len(duplicate_draw_keys))

if duplicate_full_rows:
    print()
    print("First duplicate full rows:")
    for key in duplicate_full_rows[:10]:
        print(key, "count=", full_keys[key])

if duplicate_draw_keys:
    print()
    print("First duplicate draw keys:")
    for key in duplicate_draw_keys[:10]:
        print(key, "count=", draw_keys[key])

report_path = Path("reports/data_audit_report.md")
report_path.parent.mkdir(parents=True, exist_ok=True)

with report_path.open("w", encoding="utf-8") as file:
    file.write("# Data Audit Report\n\n")
    file.write(f"Rows: {len(rows)}\n\n")
    file.write(f"Unique full rows: {len(full_keys)}\n\n")
    file.write(f"Duplicate full rows: {len(duplicate_full_rows)}\n\n")
    file.write(f"Duplicate year/draw/position keys: {len(duplicate_draw_keys)}\n\n")
    file.write("## Rows by year\n\n")
    for year in sorted(years):
        file.write(f"- {year}: {years[year]}\n")

print()
print("Report saved to:", report_path)
