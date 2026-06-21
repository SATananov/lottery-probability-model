from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "historical_draws.csv"
V41_PREDICTIONS_PATH = ROOT / "models" / "v41" / "v41_latest_predictions.json"

MODELS_DIR = ROOT / "models" / "v42"
REPORTS_DIR = ROOT / "reports"

SCORES_JSON_PATH = MODELS_DIR / "v42_positive_negative_number_scores.json"
PREDICTION_JSON_PATH = MODELS_DIR / "v42_combined_prediction.json"
SCORES_CSV_PATH = REPORTS_DIR / "v42_combined_positive_negative_scores.csv"
SUMMARY_JSON_PATH = REPORTS_DIR / "v42_combined_positive_negative_summary.json"
SUMMARY_MD_PATH = REPORTS_DIR / "v42_combined_positive_negative_summary.md"

NUMBER_COLUMN_CANDIDATES = [
    ["n1", "n2", "n3", "n4", "n5", "n6"],
    ["num1", "num2", "num3", "num4", "num5", "num6"],
    ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
]

WINDOWS = [25, 50, 100, 250, 500]


def to_int(value: Any) -> int | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return int(text)
    except ValueError:
        try:
            return int(float(text))
        except ValueError:
            return None


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def round_float(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def load_rows() -> tuple[list[dict[str, str]], list[str]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = [
            row
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]

    if not rows:
        raise ValueError("Dataset is empty.")

    columns = list(rows[0].keys())

    for candidate_columns in NUMBER_COLUMN_CANDIDATES:
        if all(column in columns for column in candidate_columns):
            return rows, candidate_columns

    raise ValueError(
        "Could not detect number columns. Expected one of: "
        + ", ".join("[" + ", ".join(columns) + "]" for columns in NUMBER_COLUMN_CANDIDATES)
    )


def build_events(rows: list[dict[str, str]], number_columns: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    invalid_rows: list[str] = []

    for row_index, row in enumerate(rows):
        numbers: list[int] = []

        for column in number_columns:
            number = to_int(row.get(column))
            if number is not None:
                numbers.append(number)

        valid_numbers = [number for number in numbers if 1 <= number <= 49]
        unique_numbers = sorted(set(valid_numbers))

        if len(unique_numbers) != 6:
            invalid_rows.append(
                f"row={row_index + 1}, numbers={numbers}, unique_valid={unique_numbers}"
            )
            continue

        event = {
            "row_index": row_index,
            "draw_id": to_int(row.get("draw_id")),
            "year": to_int(row.get("year")),
            "date": (row.get("date") or "").strip(),
            "draw_number": to_int(row.get("draw_number") or row.get("draw_no") or row.get("draw")),
            "draw_position": to_int(row.get("draw_position") or row.get("drawing_no") or row.get("position")),
            "numbers": unique_numbers,
        }
        events.append(event)

    if not events:
        raise ValueError("No valid 6/49 draw events found.")

    if all(event.get("draw_id") is not None for event in events):
        events.sort(key=lambda event: int(event["draw_id"]))
    else:
        events.sort(key=lambda event: int(event["row_index"]))

    for event_index, event in enumerate(events):
        event["event_index"] = event_index

    return events, invalid_rows


def collect_v41_votes() -> dict[int, int]:
    if not V41_PREDICTIONS_PATH.exists():
        return {number: 0 for number in range(1, 50)}

    try:
        payload = json.loads(V41_PREDICTIONS_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {number: 0 for number in range(1, 50)}

    votes: Counter[int] = Counter()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
            return

        if isinstance(node, list):
            for value in node:
                walk(value)
            return

        number = to_int(node)
        if number is not None and 1 <= number <= 49:
            votes[number] += 1

    walk(payload)
    return {number: votes[number] for number in range(1, 50)}


def compute_max_gap(positions: list[int], total_events: int) -> int:
    if not positions:
        return total_events

    max_gap = positions[0]

    for previous, current in zip(positions, positions[1:]):
        max_gap = max(max_gap, current - previous - 1)

    trailing_gap = total_events - 1 - positions[-1]
    max_gap = max(max_gap, trailing_gap)

    return max_gap


def classify_risk(score: float) -> str:
    if score >= 75:
        return "very_high"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    if score >= 25:
        return "low"
    return "very_low"


def bucket(number: int) -> int:
    return (number - 1) // 10


def select_combined_numbers(score_rows: list[dict[str, Any]]) -> list[int]:
    ranked = sorted(
        score_rows,
        key=lambda row: (
            row["combined_score"],
            row["positive_signal_score"],
            -row["absence_risk_score"],
            row["number"],
        ),
        reverse=True,
    )

    selected: list[int] = []
    bucket_counts: Counter[int] = Counter()
    odd_count = 0
    even_count = 0

    for row in ranked:
        number = int(row["number"])
        number_bucket = bucket(number)
        next_odd_count = odd_count + (number % 2)
        next_even_count = even_count + (1 if number % 2 == 0 else 0)

        if bucket_counts[number_bucket] >= 2:
            continue

        if next_odd_count > 4 or next_even_count > 4:
            continue

        selected.append(number)
        bucket_counts[number_bucket] += 1
        odd_count = next_odd_count
        even_count = next_even_count

        if len(selected) == 6:
            return sorted(selected)

    for row in ranked:
        number = int(row["number"])
        if number not in selected:
            selected.append(number)
        if len(selected) == 6:
            return sorted(selected)

    return sorted(selected)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_scores_csv(score_rows: list[dict[str, Any]]) -> None:
    SCORES_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "number",
        "total_hits",
        "expected_hits",
        "difference_from_expected",
        "frequency_ratio",
        "current_absence_gap",
        "max_absence_gap",
        "last_25_hits",
        "last_50_hits",
        "last_100_hits",
        "last_250_hits",
        "last_500_hits",
        "v41_vote_count",
        "positive_signal_score",
        "absence_risk_score",
        "combined_score",
        "absence_risk_level",
    ]

    with SCORES_CSV_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in sorted(score_rows, key=lambda item: item["number"]):
            writer.writerow({field: row.get(field) for field in fieldnames})


def write_markdown_report(summary: dict[str, Any]) -> None:
    prediction = summary["combined_prediction"]

    lines = [
        "# V42 Combined Positive/Negative Analysis Foundation",
        "",
        "This report introduces a reverse analysis layer for the lottery project.",
        "It compares positive historical signals with negative absence-risk signals.",
        "",
        "**Important:** This is not a winning guarantee. Lottery draws are random.",
        "The output is a statistical learning artifact, not a promise of future results.",
        "",
        "## Dataset",
        "",
        f"- Valid draw events analyzed: {summary['dataset']['valid_draw_events']}",
        f"- Invalid/skipped rows: {summary['dataset']['invalid_rows']}",
        f"- Expected hits per number: {summary['dataset']['expected_hits_per_number']}",
        "",
        "## Combined 6-number statistical suggestion",
        "",
        "- Numbers: " + ", ".join(str(number) for number in prediction["numbers"]),
        f"- Average positive signal: {prediction['average_positive_signal_score']}",
        f"- Average absence risk: {prediction['average_absence_risk_score']}",
        f"- Average combined score: {prediction['average_combined_score']}",
        "",
        "## Top combined-score numbers",
        "",
        "| Number | Positive score | Absence risk | Combined score | Current absence gap | Total hits |",
        "|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary["top_combined_numbers"]:
        lines.append(
            f"| {row['number']} | {row['positive_signal_score']} | "
            f"{row['absence_risk_score']} | {row['combined_score']} | "
            f"{row['current_absence_gap']} | {row['total_hits']} |"
        )

    lines.extend(
        [
            "",
            "## Numbers with high historical absence-risk signal",
            "",
            "| Number | Absence risk | Risk level | Current absence gap | Max absence gap | Total hits |",
            "|---:|---:|---|---:|---:|---:|",
        ]
    )

    for row in summary["top_absence_risk_numbers"]:
        lines.append(
            f"| {row['number']} | {row['absence_risk_score']} | "
            f"{row['absence_risk_level']} | {row['current_absence_gap']} | "
            f"{row['max_absence_gap']} | {row['total_hits']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Positive score looks for stronger historical activity and support from existing v41 outputs.",
            "- Absence-risk score looks for underrepresentation, long current gaps, and weak recent activity.",
            "- Combined score balances both sides and selects 6 numbers with simple diversification rules.",
            "- This analysis can help explain risk, but it cannot know future random lottery events.",
            "",
        ]
    )

    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    rows, number_columns = load_rows()
    events, invalid_rows = build_events(rows, number_columns)

    total_events = len(events)
    expected_hits = total_events * 6 / 49

    occurrence_counts: Counter[int] = Counter()
    positions_by_number: dict[int, list[int]] = defaultdict(list)

    for event in events:
        event_index = int(event["event_index"])

        for number in event["numbers"]:
            occurrence_counts[number] += 1
            positions_by_number[number].append(event_index)

    v41_votes = collect_v41_votes()
    max_v41_votes = max(v41_votes.values()) if v41_votes else 0

    score_rows: list[dict[str, Any]] = []

    for number in range(1, 50):
        total_hits = occurrence_counts[number]
        positions = positions_by_number[number]
        current_absence_gap = total_events - 1 - positions[-1] if positions else total_events
        max_absence_gap = compute_max_gap(positions, total_events)

        window_hits: dict[int, int] = {}
        for window in WINDOWS:
            start_index = max(0, total_events - window)
            window_hits[window] = sum(1 for position in positions if position >= start_index)

        expected_50_hits = min(50, total_events) * 6 / 49
        expected_100_hits = min(100, total_events) * 6 / 49
        expected_250_hits = min(250, total_events) * 6 / 49

        frequency_ratio = total_hits / expected_hits if expected_hits else 0.0
        difference_from_expected = total_hits - expected_hits

        frequency_strength = clamp(frequency_ratio / 1.15)
        recency_strength = 1.0 - clamp(current_absence_gap / 120)
        recent_100_strength = clamp((window_hits[100] / expected_100_hits) / 1.25) if expected_100_hits else 0.0
        recent_250_strength = clamp((window_hits[250] / expected_250_hits) / 1.25) if expected_250_hits else 0.0

        v41_support = (
            clamp(v41_votes.get(number, 0) / max_v41_votes)
            if max_v41_votes > 0
            else 0.0
        )

        positive_signal_score = 100 * (
            0.30 * frequency_strength
            + 0.20 * recency_strength
            + 0.20 * recent_100_strength
            + 0.15 * recent_250_strength
            + 0.15 * v41_support
        )

        under_expected_score = clamp((expected_hits - total_hits) / max(expected_hits * 0.15, 1))
        current_gap_score = clamp(current_absence_gap / 80)
        long_gap_score = clamp(max_absence_gap / 140)
        recent_50_under_score = clamp((expected_50_hits - window_hits[50]) / max(expected_50_hits, 1))

        absence_risk_score = 100 * (
            0.35 * under_expected_score
            + 0.30 * current_gap_score
            + 0.20 * recent_50_under_score
            + 0.15 * long_gap_score
        )

        balance_bonus = 100 * (1.0 - clamp(abs(frequency_ratio - 1.0) / 0.25))

        combined_score = (
            0.62 * positive_signal_score
            - 0.38 * absence_risk_score
            + 0.10 * balance_bonus
        )

        score_rows.append(
            {
                "number": number,
                "total_hits": int(total_hits),
                "expected_hits": round_float(expected_hits, 3),
                "difference_from_expected": round_float(difference_from_expected, 3),
                "frequency_ratio": round_float(frequency_ratio, 6),
                "current_absence_gap": int(current_absence_gap),
                "max_absence_gap": int(max_absence_gap),
                "last_25_hits": int(window_hits[25]),
                "last_50_hits": int(window_hits[50]),
                "last_100_hits": int(window_hits[100]),
                "last_250_hits": int(window_hits[250]),
                "last_500_hits": int(window_hits[500]),
                "v41_vote_count": int(v41_votes.get(number, 0)),
                "positive_signal_score": round_float(positive_signal_score, 3),
                "absence_risk_score": round_float(absence_risk_score, 3),
                "combined_score": round_float(combined_score, 3),
                "absence_risk_level": classify_risk(absence_risk_score),
            }
        )

    selected_numbers = select_combined_numbers(score_rows)
    selected_rows = [row for row in score_rows if row["number"] in selected_numbers]

    average_positive = sum(row["positive_signal_score"] for row in selected_rows) / len(selected_rows)
    average_risk = sum(row["absence_risk_score"] for row in selected_rows) / len(selected_rows)
    average_combined = sum(row["combined_score"] for row in selected_rows) / len(selected_rows)

    top_combined = sorted(score_rows, key=lambda row: row["combined_score"], reverse=True)[:12]
    top_positive = sorted(score_rows, key=lambda row: row["positive_signal_score"], reverse=True)[:12]
    top_absence_risk = sorted(score_rows, key=lambda row: row["absence_risk_score"], reverse=True)[:12]

    prediction_payload = {
        "version": "v42",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "method": "combined_positive_negative_foundation",
        "numbers": selected_numbers,
        "average_positive_signal_score": round_float(average_positive, 3),
        "average_absence_risk_score": round_float(average_risk, 3),
        "average_combined_score": round_float(average_combined, 3),
        "selected_number_details": sorted(selected_rows, key=lambda row: row["number"]),
        "important_warning": (
            "This is a statistical analysis artifact, not a winning guarantee. "
            "Lottery draws are random."
        ),
    }

    scores_payload = {
        "version": "v42",
        "created_at": prediction_payload["created_at"],
        "dataset": {
            "source": str(DATA_PATH.relative_to(ROOT)),
            "valid_draw_events": total_events,
            "invalid_rows": len(invalid_rows),
            "number_columns": number_columns,
            "expected_hits_per_number": round_float(expected_hits, 3),
            "uses_bonus": False,
        },
        "score_explanation": {
            "positive_signal_score": (
                "Frequency, recency, recent-window activity, and v41 vote support."
            ),
            "absence_risk_score": (
                "Underrepresentation, current absence gap, weak recent activity, and long historical gaps."
            ),
            "combined_score": (
                "Positive signal minus absence-risk pressure, with a small balance bonus."
            ),
        },
        "numbers": sorted(score_rows, key=lambda row: row["number"]),
    }

    summary_payload = {
        "version": "v42",
        "created_at": prediction_payload["created_at"],
        "dataset": scores_payload["dataset"],
        "combined_prediction": prediction_payload,
        "top_combined_numbers": top_combined,
        "top_positive_signal_numbers": top_positive,
        "top_absence_risk_numbers": top_absence_risk,
        "important_warning": prediction_payload["important_warning"],
    }

    write_json(SCORES_JSON_PATH, scores_payload)
    write_json(PREDICTION_JSON_PATH, prediction_payload)
    write_json(SUMMARY_JSON_PATH, summary_payload)
    write_scores_csv(score_rows)
    write_markdown_report(summary_payload)

    print("V42_FOUNDATION_DONE")
    print("valid_draw_events", total_events)
    print("invalid_rows", len(invalid_rows))
    print("expected_hits_per_number", round_float(expected_hits, 3))
    print("combined_numbers", selected_numbers)
    print("average_positive_signal_score", prediction_payload["average_positive_signal_score"])
    print("average_absence_risk_score", prediction_payload["average_absence_risk_score"])
    print("average_combined_score", prediction_payload["average_combined_score"])
    print("scores_json", SCORES_JSON_PATH.relative_to(ROOT).as_posix())
    print("prediction_json", PREDICTION_JSON_PATH.relative_to(ROOT).as_posix())
    print("summary_md", SUMMARY_MD_PATH.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
