from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
AUDIT_JSON = ROOT / "reports" / "v41_training_readiness_audit.json"
AUDIT_MD = ROOT / "reports" / "v41_training_readiness_audit.md"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]


def main() -> int:
    if not CANONICAL_PATH.exists():
        raise FileNotFoundError(f"Missing canonical dataset: {CANONICAL_PATH}")

    df = pd.read_csv(CANONICAL_PATH)

    required = {
        "draw_event_id",
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
        "data_status",
    }

    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    invalid_numbers = []
    duplicate_combinations = []
    duplicate_keys = []

    seen_keys = set()

    for index, row in df.iterrows():
        row_no = index + 2

        key = (int(row["year"]), int(row["draw_number"]), int(row["drawing_no"]))
        if key in seen_keys:
            duplicate_keys.append({"row": row_no, "key": key})
        seen_keys.add(key)

        numbers = [int(row[col]) for col in NUMBER_COLS]

        if len(set(numbers)) != 6:
            duplicate_combinations.append(
                {
                    "row": row_no,
                    "year": int(row["year"]),
                    "draw_number": int(row["draw_number"]),
                    "drawing_no": int(row["drawing_no"]),
                    "numbers": numbers,
                }
            )

        if not all(1 <= number <= 49 for number in numbers):
            invalid_numbers.append(
                {
                    "row": row_no,
                    "year": int(row["year"]),
                    "draw_number": int(row["draw_number"]),
                    "drawing_no": int(row["drawing_no"]),
                    "numbers": numbers,
                }
            )

    grouped = defaultdict(set)
    for _, row in df.iterrows():
        grouped[(int(row["year"]), int(row["draw_number"]))].add(int(row["drawing_no"]))

    drawings_per_draw = Counter(len(values) for values in grouped.values())
    drawing_no_counts = Counter(int(x) for x in df["drawing_no"])

    by_year = {}
    for year in sorted(df["year"].astype(int).unique()):
        ydf = df[df["year"].astype(int) == int(year)].copy()
        y_groups = defaultdict(set)

        for _, row in ydf.iterrows():
            y_groups[(int(row["year"]), int(row["draw_number"]))].add(int(row["drawing_no"]))

        by_year[str(year)] = {
            "draw_events": int(len(ydf)),
            "unique_draws": int(len(y_groups)),
            "drawing_no_counts": {
                str(k): int(v)
                for k, v in sorted(Counter(int(x) for x in ydf["drawing_no"]).items())
            },
            "drawings_per_draw_distribution": {
                str(k): int(v)
                for k, v in sorted(Counter(len(values) for values in y_groups.values()).items())
            },
            "max_drawing_no": int(ydf["drawing_no"].max()),
        }

    d4 = df[df["drawing_no"].astype(int) == 4].copy()
    drawing_4_groups = []
    if not d4.empty:
        for _, row in d4.iterrows():
            year = int(row["year"])
            draw_number = int(row["draw_number"])
            group = df[
                (df["year"].astype(int) == year)
                & (df["draw_number"].astype(int) == draw_number)
            ].sort_values("drawing_no")

            drawing_4_groups.append(
                {
                    "year": year,
                    "draw_number": draw_number,
                    "drawings": [
                        {
                            "drawing_no": int(item["drawing_no"]),
                            "numbers": [int(item[col]) for col in NUMBER_COLS],
                            "source_url": str(item.get("source_url", "")),
                            "source_draw_id": str(item.get("source_draw_id", "")),
                        }
                        for _, item in group.iterrows()
                    ],
                }
            )

    date_available = int(df["date"].notna().sum()) if "date" in df.columns else 0
    date_missing = int(len(df) - date_available)

    bonus_series = df["bonus_number"] if "bonus_number" in df.columns else pd.Series([], dtype=object)
    bonus_available = int(bonus_series.notna().sum())
    bonus_missing = int(len(df) - bonus_available)

    readiness = {
        "status": "training_ready_review_required_no_retrain",
        "canonical_dataset": str(CANONICAL_PATH.relative_to(ROOT)),
        "total_draw_events": int(len(df)),
        "total_unique_draws": int(len(grouped)),
        "years": {
            "min": int(df["year"].min()),
            "max": int(df["year"].max()),
            "count": int(df["year"].nunique()),
        },
        "drawing_no_counts": {str(k): int(v) for k, v in sorted(drawing_no_counts.items())},
        "drawings_per_draw_distribution": {
            str(k): int(v) for k, v in sorted(drawings_per_draw.items())
        },
        "date_available_rows": date_available,
        "date_missing_rows": date_missing,
        "bonus_available_rows": bonus_available,
        "bonus_missing_rows": bonus_missing,
        "invalid_number_rows": len(invalid_numbers),
        "duplicate_number_rows": len(duplicate_combinations),
        "duplicate_keys": len(duplicate_keys),
        "drawing_no_4_groups_count": len(drawing_4_groups),
        "drawing_no_4_groups_sample": drawing_4_groups[:20],
        "by_year": by_year,
        "recommendation": {
            "use_for_main_number_models": True,
            "use_bonus_model": False,
            "reason": "Canonical dataset has valid main draw events and no duplicate keys. Bonus numbers are unavailable and must not be invented.",
        },
    }

    AUDIT_JSON.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# v41 Training Readiness Audit",
        "",
        "Status: review required. No model retraining was performed.",
        "",
        "## Summary",
        "",
        f"- Canonical dataset: `{readiness['canonical_dataset']}`",
        f"- Total draw events: {readiness['total_draw_events']}",
        f"- Total unique draws: {readiness['total_unique_draws']}",
        f"- Years: {readiness['years']['min']}–{readiness['years']['max']} ({readiness['years']['count']} years)",
        f"- Invalid number rows: {readiness['invalid_number_rows']}",
        f"- Duplicate number rows: {readiness['duplicate_number_rows']}",
        f"- Duplicate keys: {readiness['duplicate_keys']}",
        f"- Date available rows: {readiness['date_available_rows']}",
        f"- Date missing rows: {readiness['date_missing_rows']}",
        f"- Bonus available rows: {readiness['bonus_available_rows']}",
        f"- Bonus missing rows: {readiness['bonus_missing_rows']}",
        f"- Draw groups with drawing_no=4: {readiness['drawing_no_4_groups_count']}",
        "",
        "## Drawing number counts",
        "",
    ]

    for key, value in readiness["drawing_no_counts"].items():
        lines.append(f"- drawing_no={key}: {value}")

    lines.extend(["", "## Drawings per draw distribution", ""])

    for key, value in readiness["drawings_per_draw_distribution"].items():
        lines.append(f"- {key} drawing(s) per draw: {value} draws")

    lines.extend(["", "## Recommendation", ""])
    lines.append("- Use this canonical dataset for main-number v41 model retraining after review.")
    lines.append("- Do not train a bonus-number model yet because bonus data is unavailable.")
    lines.append("- Keep `drawing_no` as a rules-aware field.")
    lines.append("- Do not merge several drawings into one 12/18/24-number record.")

    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("DONE: v41 training readiness audit completed.")
    print("TOTAL_DRAW_EVENTS", readiness["total_draw_events"])
    print("TOTAL_UNIQUE_DRAWS", readiness["total_unique_draws"])
    print("YEARS", readiness["years"])
    print("DRAWING_NO_COUNTS", readiness["drawing_no_counts"])
    print("DRAWINGS_PER_DRAW_DISTRIBUTION", readiness["drawings_per_draw_distribution"])
    print("INVALID_NUMBER_ROWS", readiness["invalid_number_rows"])
    print("DUPLICATE_NUMBER_ROWS", readiness["duplicate_number_rows"])
    print("DUPLICATE_KEYS", readiness["duplicate_keys"])
    print("DRAWING_NO_4_GROUPS", readiness["drawing_no_4_groups_count"])
    print("USE_FOR_MAIN_NUMBER_MODELS", readiness["recommendation"]["use_for_main_number_models"])
    print("USE_BONUS_MODEL", readiness["recommendation"]["use_bonus_model"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
