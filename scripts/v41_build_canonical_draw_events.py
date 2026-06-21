from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SOURCE_PATH = ROOT / "data" / "historical_draws.csv"
OUT_DATA = ROOT / "data" / "v41_canonical_draw_events.csv"
OUT_AUDIT_JSON = ROOT / "reports" / "v41_canonical_draw_events_audit.json"
OUT_AUDIT_MD = ROOT / "reports" / "v41_canonical_draw_events_audit.md"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "nat"}:
        return ""

    return text


def parse_int(value: Any, field: str, row_number: int) -> int:
    text = clean_text(value)

    if not text:
        raise ValueError(f"Missing integer value for {field} at source row {row_number}")

    try:
        return int(float(text))
    except ValueError as exc:
        raise ValueError(f"Invalid integer value for {field} at source row {row_number}: {value!r}") from exc


def read_historical_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing source dataset: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("Source dataset is empty.")

    required = {"year", "draw_number", "n1", "n2", "n3", "n4", "n5", "n6"}
    fields = set(rows[0].keys())

    missing = sorted(required - fields)
    if missing:
        raise ValueError(f"Missing required source columns: {missing}")

    return rows


def build_canonical(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    canonical: list[dict[str, Any]] = []

    invalid_rows: list[dict[str, Any]] = []
    duplicate_keys: list[dict[str, Any]] = []
    seen_keys: set[tuple[int, int, int]] = set()

    for row_index, row in enumerate(rows, start=2):
        try:
            year = parse_int(row.get("year"), "year", row_index)
            draw_number = parse_int(row.get("draw_number"), "draw_number", row_index)

            if "draw_position" in row and clean_text(row.get("draw_position")):
                drawing_no = parse_int(row.get("draw_position"), "draw_position", row_index)
            else:
                drawing_no = 1

            numbers = [parse_int(row.get(col), col, row_index) for col in NUMBER_COLS]

            if len(numbers) != 6:
                raise ValueError("Expected exactly 6 numbers.")

            if len(set(numbers)) != 6:
                raise ValueError(f"Duplicate numbers in draw event: {numbers}")

            if not all(1 <= number <= 49 for number in numbers):
                raise ValueError(f"Numbers outside 1..49: {numbers}")

            if drawing_no < 1:
                raise ValueError(f"Invalid drawing_no: {drawing_no}")

            key = (year, draw_number, drawing_no)

            if key in seen_keys:
                duplicate_keys.append(
                    {
                        "source_row": row_index,
                        "year": year,
                        "draw_number": draw_number,
                        "drawing_no": drawing_no,
                    }
                )
            else:
                seen_keys.add(key)

            date_value = clean_text(row.get("date"))
            source_url = clean_text(row.get("source_url"))
            source_draw_id = clean_text(row.get("draw_id"))

            canonical.append(
                {
                    "draw_event_id": f"{year}-{draw_number}-{drawing_no}",
                    "year": year,
                    "draw_number": draw_number,
                    "date": date_value,
                    "drawing_no": drawing_no,
                    "n1": numbers[0],
                    "n2": numbers[1],
                    "n3": numbers[2],
                    "n4": numbers[3],
                    "n5": numbers[4],
                    "n6": numbers[5],
                    "bonus_number": "",
                    "source": "historical_draws.csv",
                    "source_url": source_url,
                    "source_draw_id": source_draw_id,
                    "data_status": "available_without_bonus",
                }
            )

        except Exception as exc:
            invalid_rows.append(
                {
                    "source_row": row_index,
                    "error": str(exc),
                    "raw": row,
                }
            )

    canonical.sort(
        key=lambda item: (
            int(item["year"]),
            int(item["draw_number"]),
            int(item["drawing_no"]),
        )
    )

    diagnostics = {
        "invalid_rows": invalid_rows,
        "duplicate_keys": duplicate_keys,
    }

    return canonical, diagnostics


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "draw_event_id",
        "year",
        "draw_number",
        "date",
        "drawing_no",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
        "bonus_number",
        "source",
        "source_url",
        "source_draw_id",
        "data_status",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_audit(rows: list[dict[str, Any]], diagnostics: dict[str, Any]) -> dict[str, Any]:
    if not rows:
        raise ValueError("No canonical rows were built.")

    drawing_no_counts = Counter(int(row["drawing_no"]) for row in rows)

    grouped_drawings: dict[tuple[int, int], set[int]] = defaultdict(set)
    for row in rows:
        grouped_drawings[(int(row["year"]), int(row["draw_number"]))].add(int(row["drawing_no"]))

    drawings_per_draw_distribution = Counter(len(values) for values in grouped_drawings.values())

    by_year: dict[str, dict[str, Any]] = {}

    years = sorted({int(row["year"]) for row in rows})

    for year in years:
        year_rows = [row for row in rows if int(row["year"]) == year]
        year_draw_keys = sorted(
            {
                (int(row["year"]), int(row["draw_number"]))
                for row in year_rows
            }
        )

        year_distribution = Counter(len(grouped_drawings[key]) for key in year_draw_keys)

        by_year[str(year)] = {
            "draw_events": len(year_rows),
            "unique_draws": len(year_draw_keys),
            "drawing_no_counts": dict(
                sorted(Counter(int(row["drawing_no"]) for row in year_rows).items())
            ),
            "drawings_per_draw_distribution": dict(sorted(year_distribution.items())),
            "max_drawing_no": max(int(row["drawing_no"]) for row in year_rows),
            "date_available_rows": sum(1 for row in year_rows if clean_text(row.get("date"))),
            "bonus_available_rows": sum(1 for row in year_rows if clean_text(row.get("bonus_number"))),
        }

    audit = {
        "status": "canonical_dataset_built_no_model_retrain",
        "source_dataset": str(SOURCE_PATH.relative_to(ROOT)),
        "canonical_dataset": str(OUT_DATA.relative_to(ROOT)),
        "total_draw_events": len(rows),
        "total_unique_draws": len(grouped_drawings),
        "years": {
            "min": min(years),
            "max": max(years),
            "count": len(years),
        },
        "drawing_no_counts": dict(sorted(drawing_no_counts.items())),
        "drawings_per_draw_distribution": dict(sorted(drawings_per_draw_distribution.items())),
        "date_available_rows": sum(1 for row in rows if clean_text(row.get("date"))),
        "date_missing_rows": sum(1 for row in rows if not clean_text(row.get("date"))),
        "bonus_available_rows": sum(1 for row in rows if clean_text(row.get("bonus_number"))),
        "bonus_missing_rows": sum(1 for row in rows if not clean_text(row.get("bonus_number"))),
        "invalid_rows_count": len(diagnostics["invalid_rows"]),
        "duplicate_keys_count": len(diagnostics["duplicate_keys"]),
        "invalid_rows_sample": diagnostics["invalid_rows"][:20],
        "duplicate_keys_sample": diagnostics["duplicate_keys"][:20],
        "by_year": by_year,
    }

    return audit


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines: list[str] = []

    lines.append("# v41 Canonical Rules-Aware Draw Events Audit")
    lines.append("")
    lines.append("Status: canonical dataset built. No model retraining was performed.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Source dataset: `{audit['source_dataset']}`")
    lines.append(f"- Canonical dataset: `{audit['canonical_dataset']}`")
    lines.append(f"- Total draw events: {audit['total_draw_events']}")
    lines.append(f"- Total unique draws: {audit['total_unique_draws']}")
    lines.append(f"- Years: {audit['years']['min']}–{audit['years']['max']} ({audit['years']['count']} years)")
    lines.append(f"- Date available rows: {audit['date_available_rows']}")
    lines.append(f"- Date missing rows: {audit['date_missing_rows']}")
    lines.append(f"- Bonus available rows: {audit['bonus_available_rows']}")
    lines.append(f"- Bonus missing rows: {audit['bonus_missing_rows']}")
    lines.append(f"- Invalid rows: {audit['invalid_rows_count']}")
    lines.append(f"- Duplicate keys: {audit['duplicate_keys_count']}")
    lines.append("")
    lines.append("## Drawing number counts")
    lines.append("")

    for drawing_no, count in audit["drawing_no_counts"].items():
        lines.append(f"- drawing_no={drawing_no}: {count}")

    lines.append("")
    lines.append("## Drawings per draw distribution")
    lines.append("")

    for drawing_count, draw_count in audit["drawings_per_draw_distribution"].items():
        lines.append(f"- {drawing_count} drawing(s) per draw: {draw_count} draws")

    lines.append("")
    lines.append("## By year")
    lines.append("")
    lines.append("| Year | Draw events | Unique draws | Drawings per draw | Max drawing_no |")
    lines.append("|---:|---:|---:|---|---:|")

    for year, info in audit["by_year"].items():
        lines.append(
            f"| {year} | {info['draw_events']} | {info['unique_draws']} | "
            f"{info['drawings_per_draw_distribution']} | {info['max_drawing_no']} |"
        )

    lines.append("")
    lines.append("## Important notes")
    lines.append("")
    lines.append("- Each row is treated as one real draw event.")
    lines.append("- `drawing_no` is derived from `draw_position` in the source dataset.")
    lines.append("- Bonus numbers are not invented; they remain missing until a reliable source is added.")
    lines.append("- This dataset is ready for review before v41 model retraining.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    source_rows = read_historical_rows(SOURCE_PATH)
    canonical_rows, diagnostics = build_canonical(source_rows)

    if diagnostics["invalid_rows"]:
        print("ERROR: Invalid source rows found. First examples:")
        for item in diagnostics["invalid_rows"][:10]:
            print(item)
        return 1

    if diagnostics["duplicate_keys"]:
        print("ERROR: Duplicate canonical keys found. First examples:")
        for item in diagnostics["duplicate_keys"][:10]:
            print(item)
        return 1

    write_csv(OUT_DATA, canonical_rows)

    audit = build_audit(canonical_rows, diagnostics)

    OUT_AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(OUT_AUDIT_MD, audit)

    print("DONE: v41 canonical rules-aware dataset built.")
    print("CANONICAL_DATASET", OUT_DATA)
    print("AUDIT_JSON", OUT_AUDIT_JSON)
    print("AUDIT_MD", OUT_AUDIT_MD)
    print("TOTAL_DRAW_EVENTS", audit["total_draw_events"])
    print("TOTAL_UNIQUE_DRAWS", audit["total_unique_draws"])
    print("YEARS", audit["years"]["min"], audit["years"]["max"])
    print("DRAWING_NO_COUNTS", audit["drawing_no_counts"])
    print("DRAWINGS_PER_DRAW_DISTRIBUTION", audit["drawings_per_draw_distribution"])
    print("DATE_AVAILABLE_ROWS", audit["date_available_rows"])
    print("DATE_MISSING_ROWS", audit["date_missing_rows"])
    print("BONUS_AVAILABLE_ROWS", audit["bonus_available_rows"])
    print("BONUS_MISSING_ROWS", audit["bonus_missing_rows"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
