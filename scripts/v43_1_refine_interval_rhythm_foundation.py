from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "historical_draws.csv"

SCORES_JSON = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_scores.json"
PREDICTION_JSON = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_prediction.json"
SUMMARY_JSON = ROOT / "reports" / "v43_1_interval_rhythm_refined_summary.json"
SCORES_CSV = ROOT / "reports" / "v43_1_interval_rhythm_refined_scores.csv"
SUMMARY_MD = ROOT / "reports" / "v43_1_interval_rhythm_refined_summary.md"


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [
            row
            for row in csv.DictReader(f)
            if any((value or "").strip() for value in row.values())
        ]


def detect_main_number_columns(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        raise ValueError("Dataset is empty.")

    columns = list(rows[0].keys())
    preferred = [f"n{i}" for i in range(1, 7)]

    if all(col in columns for col in preferred):
        return preferred

    raise ValueError("Expected columns n1, n2, n3, n4, n5, n6.")


def parse_valid_events(rows: list[dict[str, str]], number_cols: list[str]) -> list[dict[str, Any]]:
    events = []

    for raw_index, row in enumerate(rows, start=1):
        numbers = []

        for col in number_cols:
            try:
                numbers.append(int((row.get(col) or "").strip()))
            except ValueError:
                numbers.append(-1)

        if len(numbers) != 6:
            continue

        if len(set(numbers)) != 6:
            continue

        if not all(1 <= number <= 49 for number in numbers):
            continue

        events.append(
            {
                "event_index": len(events) + 1,
                "raw_index": raw_index,
                "date": row.get("date", ""),
                "year": row.get("year", ""),
                "draw_number": row.get("draw_number", ""),
                "numbers": sorted(numbers),
            }
        )

    return events


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None

    ordered = sorted(values)

    if len(ordered) == 1:
        return float(ordered[0])

    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return float(ordered[int(position)])

    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def most_common_interval(intervals: list[int]) -> int | None:
    if not intervals:
        return None

    counts = Counter(intervals)
    best_count = max(counts.values())
    best_values = [value for value, count in counts.items() if count == best_count]
    return min(best_values)


def safe_round(value: float | int | None, digits: int = 3) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def bounded(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def sigmoid(value: float) -> float:
    if value > 60:
        return 1.0
    if value < -60:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def rhythm_status(current_gap: int, p25: float | None, p75: float | None, p90: float | None, max_gap: int | None) -> str:
    if p25 is None or p75 is None or p90 is None or max_gap is None:
        return "insufficient_history"

    if current_gap <= p25:
        return "early"
    if current_gap <= p75:
        return "normal"
    if current_gap <= p90:
        return "watch_zone"
    if current_gap <= max_gap:
        return "late"
    return "beyond_historical_gap"


def conditional_window_probability(intervals: list[int], current_gap: int, window: int) -> tuple[float | None, int, int]:
    survived = [value for value in intervals if value > current_gap]

    if not survived:
        return None, 0, 0

    hits_in_window = [value for value in survived if value <= current_gap + window]
    return len(hits_in_window) / len(survived), len(hits_in_window), len(survived)


def expected_remaining_wait(intervals: list[int], current_gap: int) -> tuple[float | None, float | None]:
    remaining = [value - current_gap for value in intervals if value > current_gap]

    if not remaining:
        return None, None

    return mean(remaining), median(remaining)


def reliability_score(survival_count: int, interval_count: int) -> float:
    if interval_count <= 0:
        return 0.0

    sample_strength = min(1.0, interval_count / 300.0)
    survival_strength = min(1.0, survival_count / 80.0)

    return bounded((0.65 * sample_strength + 0.35 * survival_strength) * 100)


def build_number_stats(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_draws = len(events)
    expected_hits = total_draws * 6 / 49

    positions_by_number: dict[int, list[int]] = {number: [] for number in range(1, 50)}

    for event in events:
        event_index = int(event["event_index"])
        for number in event["numbers"]:
            positions_by_number[number].append(event_index)

    rows = []

    for number in range(1, 50):
        positions = positions_by_number[number]
        intervals = [
            positions[index] - positions[index - 1]
            for index in range(1, len(positions))
        ]

        total_hits = len(positions)
        interval_count = len(intervals)
        last_seen_draw = positions[-1] if positions else None
        current_gap = total_draws - last_seen_draw if last_seen_draw is not None else total_draws

        average_interval = mean(intervals) if intervals else None
        median_interval = median(intervals) if intervals else None
        std_interval = pstdev(intervals) if len(intervals) >= 2 else 0.0
        min_interval = min(intervals) if intervals else None
        max_interval = max(intervals) if intervals else None
        mode_interval = most_common_interval(intervals)

        p25 = percentile([float(value) for value in intervals], 0.25)
        p75 = percentile([float(value) for value in intervals], 0.75)
        p90 = percentile([float(value) for value in intervals], 0.90)

        p_next_1, hits_next_1, survived_next_1 = conditional_window_probability(intervals, current_gap, 1)
        p_next_3, hits_next_3, survived_next_3 = conditional_window_probability(intervals, current_gap, 3)
        p_next_5, hits_next_5, survived_next_5 = conditional_window_probability(intervals, current_gap, 5)
        p_next_10, hits_next_10, survived_next_10 = conditional_window_probability(intervals, current_gap, 10)

        expected_remaining_mean, expected_remaining_median = expected_remaining_wait(intervals, current_gap)

        if average_interval and average_interval > 0 and std_interval > 0:
            z_score = (current_gap - average_interval) / std_interval
            due_score = sigmoid(z_score) * 100
        elif average_interval and average_interval > 0:
            z_score = 0.0
            due_score = 50.0
        else:
            z_score = None
            due_score = 0.0

        if median_interval and median_interval > 0:
            closeness_to_median = bounded(100 - (abs(current_gap - median_interval) / median_interval) * 100)
            above_median_ratio = current_gap / median_interval
        else:
            closeness_to_median = 0.0
            above_median_ratio = None

        if average_interval and average_interval > 0:
            coefficient_of_variation = std_interval / average_interval
            regularity = 100 / (1 + coefficient_of_variation)
        else:
            coefficient_of_variation = None
            regularity = 0.0

        frequency_ratio = total_hits / expected_hits if expected_hits else 0.0
        frequency_support = bounded(50 + (frequency_ratio - 1) * 100)

        status = rhythm_status(current_gap, p25, p75, p90, max_interval)

        next_3_component = (p_next_3 * 100) if p_next_3 is not None else 0.0
        next_5_component = (p_next_5 * 100) if p_next_5 is not None else 0.0
        next_10_component = (p_next_10 * 100) if p_next_10 is not None else 0.0
        reliability = reliability_score(survived_next_5, interval_count)

        late_bonus = 0.0
        if status == "watch_zone":
            late_bonus = 8.0
        elif status == "late":
            late_bonus = 14.0
        elif status == "beyond_historical_gap":
            late_bonus = 18.0
        elif status == "early":
            late_bonus = -12.0

        balanced_rhythm_score = bounded(
            0.30 * next_5_component
            + 0.25 * due_score
            + 0.20 * closeness_to_median
            + 0.15 * regularity
            + 0.10 * frequency_support
        )

        next_window_score = bounded(
            0.38 * next_5_component
            + 0.22 * next_3_component
            + 0.18 * due_score
            + 0.10 * reliability
            + 0.07 * frequency_support
            + late_bonus
        )

        overdue_score = bounded(
            0.35 * due_score
            + 0.25 * next_10_component
            + 0.20 * reliability
            + 0.10 * frequency_support
            + max(0.0, late_bonus)
            - (8.0 if status == "early" else 0.0)
        )

        final_rhythm_score = bounded(
            0.50 * next_window_score
            + 0.30 * balanced_rhythm_score
            + 0.20 * overdue_score
        )

        rows.append(
            {
                "number": number,
                "total_hits": total_hits,
                "last_seen_draw": last_seen_draw,
                "current_gap": current_gap,
                "average_interval": safe_round(average_interval),
                "median_interval": safe_round(median_interval),
                "mode_interval": mode_interval,
                "std_interval": safe_round(std_interval),
                "coefficient_of_variation": safe_round(coefficient_of_variation),
                "min_interval": min_interval,
                "max_interval": max_interval,
                "p25_interval": safe_round(p25),
                "p75_interval": safe_round(p75),
                "p90_interval": safe_round(p90),
                "expected_remaining_mean": safe_round(expected_remaining_mean),
                "expected_remaining_median": safe_round(expected_remaining_median),
                "probability_next_1_draw": safe_round(p_next_1),
                "probability_next_3_draws": safe_round(p_next_3),
                "probability_next_5_draws": safe_round(p_next_5),
                "probability_next_10_draws": safe_round(p_next_10),
                "survived_intervals_for_next_5": survived_next_5,
                "hits_in_next_5_window": hits_next_5,
                "z_score_vs_average_interval": safe_round(z_score),
                "above_median_ratio": safe_round(above_median_ratio),
                "due_score": safe_round(due_score),
                "closeness_to_median_score": safe_round(closeness_to_median),
                "regularity_score": safe_round(regularity),
                "reliability_score": safe_round(reliability),
                "frequency_ratio": safe_round(frequency_ratio),
                "frequency_support_score": safe_round(frequency_support),
                "balanced_rhythm_score": safe_round(balanced_rhythm_score),
                "next_window_score": safe_round(next_window_score),
                "overdue_score": safe_round(overdue_score),
                "final_rhythm_score": safe_round(final_rhythm_score),
                "rhythm_status": status,
                "beyond_historical_gap": bool(max_interval is not None and current_gap > max_interval),
            }
        )

    return rows


def bucket_for_number(number: int) -> int:
    if number <= 9:
        return 0
    if number <= 19:
        return 1
    if number <= 29:
        return 2
    if number <= 39:
        return 3
    return 4


def select_six_numbers(rows: list[dict[str, Any]], score_key: str) -> list[int]:
    ranked = sorted(
        rows,
        key=lambda row: (
            float(row.get(score_key) or 0),
            float(row.get("probability_next_5_draws") or 0),
            float(row.get("due_score") or 0),
            int(row.get("current_gap") or 0),
        ),
        reverse=True,
    )

    selected: list[int] = []
    bucket_counts: dict[int, int] = {}
    parity_counts = {0: 0, 1: 0}

    for row in ranked:
        number = int(row["number"])
        bucket = bucket_for_number(number)
        parity = number % 2

        if bucket_counts.get(bucket, 0) >= 2:
            continue

        if parity_counts[parity] >= 4:
            continue

        selected.append(number)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        parity_counts[parity] += 1

        if len(selected) == 6:
            break

    return sorted(selected)


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        raise ValueError("No rows to write.")

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]], columns: list[str], limit: int = 12) -> str:
    selected = rows[:limit]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, separator]

    for row in selected:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")

    return "\n".join(lines)


def build_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Interval Rhythm Refined Foundation Report",
        "",
        "This report studies the historical interval rhythm of each main lottery number.",
        "",
        "**Important:** This is statistical analysis, not a winning guarantee. Lottery draws are random.",
        "",
        f"Valid historical draws analyzed: **{summary['valid_draws']}**",
        f"Bonus number used: **{summary['uses_bonus']}**",
        "",
        "## Suggested number sets",
        "",
        f"Balanced rhythm: {', '.join(str(n) for n in summary['balanced_rhythm_numbers'])}",
        f"Next-window rhythm: {', '.join(str(n) for n in summary['next_window_numbers'])}",
        f"Overdue watchlist: {', '.join(str(n) for n in summary['overdue_watchlist_numbers'])}",
        f"Final refined rhythm: {', '.join(str(n) for n in summary['final_refined_rhythm_numbers'])}",
        "",
        "## Top next-window rhythm numbers",
        "",
        markdown_table(
            summary["top_next_window_numbers"],
            [
                "number",
                "next_window_score",
                "current_gap",
                "median_interval",
                "probability_next_3_draws",
                "probability_next_5_draws",
                "expected_remaining_median",
                "rhythm_status",
            ],
        ),
        "",
        "## Top balanced rhythm numbers",
        "",
        markdown_table(
            summary["top_balanced_numbers"],
            [
                "number",
                "balanced_rhythm_score",
                "current_gap",
                "median_interval",
                "probability_next_5_draws",
                "rhythm_status",
            ],
        ),
        "",
        "## Overdue watchlist",
        "",
        markdown_table(
            summary["top_overdue_numbers"],
            [
                "number",
                "overdue_score",
                "current_gap",
                "average_interval",
                "median_interval",
                "max_interval",
                "rhythm_status",
            ],
        ),
        "",
        "## How to read this refinement",
        "",
        "- `balanced_rhythm_score` favors numbers near their usual historical rhythm.",
        "- `next_window_score` favors numbers with a stronger empirical signal for the next 3–5 draws.",
        "- `overdue_score` highlights numbers that are late compared with their own rhythm.",
        "- `final_rhythm_score` combines all three views.",
        "- These are statistical indicators, not guarantees.",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    raw_rows = load_rows(DATA_PATH)
    number_cols = detect_main_number_columns(raw_rows)
    events = parse_valid_events(raw_rows, number_cols)

    if len(events) != 10057:
        raise RuntimeError(f"Expected 10057 valid events, got {len(events)}")

    score_rows = build_number_stats(events)

    balanced_numbers = select_six_numbers(score_rows, "balanced_rhythm_score")
    next_window_numbers = select_six_numbers(score_rows, "next_window_score")
    overdue_numbers = select_six_numbers(score_rows, "overdue_score")
    final_numbers = select_six_numbers(score_rows, "final_rhythm_score")

    metadata = {
        "model_name": "interval_rhythm_refined_foundation",
        "internal_version": "v43.1",
        "purpose": "Compare balanced rhythm, next-window rhythm, and overdue rhythm signals for the 49 main numbers.",
        "important_warning": "This is a statistical analysis artifact, not a winning guarantee. Lottery draws are random.",
        "uses_bonus": False,
        "valid_draws": len(events),
        "number_columns": number_cols,
        "total_numbers_scored": len(score_rows),
    }

    sorted_balanced = sorted(score_rows, key=lambda row: float(row.get("balanced_rhythm_score") or 0), reverse=True)
    sorted_next_window = sorted(score_rows, key=lambda row: float(row.get("next_window_score") or 0), reverse=True)
    sorted_overdue = sorted(score_rows, key=lambda row: float(row.get("overdue_score") or 0), reverse=True)
    sorted_final = sorted(score_rows, key=lambda row: float(row.get("final_rhythm_score") or 0), reverse=True)

    scores_payload = {
        **metadata,
        "numbers": score_rows,
    }

    prediction_payload = {
        **metadata,
        "balanced_rhythm_numbers": balanced_numbers,
        "next_window_numbers": next_window_numbers,
        "overdue_watchlist_numbers": overdue_numbers,
        "final_refined_rhythm_numbers": final_numbers,
        "selected_number_details": [row for row in score_rows if int(row["number"]) in final_numbers],
        "selection_method": "Separate score views with simple decade/parity diversification.",
    }

    summary_payload = {
        **metadata,
        "balanced_rhythm_numbers": balanced_numbers,
        "next_window_numbers": next_window_numbers,
        "overdue_watchlist_numbers": overdue_numbers,
        "final_refined_rhythm_numbers": final_numbers,
        "top_balanced_numbers": sorted_balanced[:12],
        "top_next_window_numbers": sorted_next_window[:12],
        "top_overdue_numbers": sorted_overdue[:12],
        "top_final_numbers": sorted_final[:12],
    }

    write_json(scores_payload, SCORES_JSON)
    write_json(prediction_payload, PREDICTION_JSON)
    write_json(summary_payload, SUMMARY_JSON)
    write_csv(score_rows, SCORES_CSV)
    SUMMARY_MD.write_text(build_summary_markdown(summary_payload), encoding="utf-8")

    print("BALANCED_RHYTHM_NUMBERS", balanced_numbers)
    print("NEXT_WINDOW_NUMBERS", next_window_numbers)
    print("OVERDUE_WATCHLIST_NUMBERS", overdue_numbers)
    print("FINAL_REFINED_RHYTHM_NUMBERS", final_numbers)
    print("VALID_DRAWS", len(events))
    print("USES_BONUS", False)
    print("SCORED_NUMBERS", len(score_rows))
    print("FILES_CREATED")
    print(SCORES_JSON.relative_to(ROOT))
    print(PREDICTION_JSON.relative_to(ROOT))
    print(SUMMARY_JSON.relative_to(ROOT))
    print(SCORES_CSV.relative_to(ROOT))
    print(SUMMARY_MD.relative_to(ROOT))

    print("TOP_NEXT_WINDOW")
    for row in sorted_next_window[:12]:
        print(
            row["number"],
            "next=", row["next_window_score"],
            "gap=", row["current_gap"],
            "median=", row["median_interval"],
            "p3=", row["probability_next_3_draws"],
            "p5=", row["probability_next_5_draws"],
            "remain_med=", row["expected_remaining_median"],
            "status=", row["rhythm_status"],
        )

    print("TOP_OVERDUE")
    for row in sorted_overdue[:12]:
        print(
            row["number"],
            "overdue=", row["overdue_score"],
            "gap=", row["current_gap"],
            "avg=", row["average_interval"],
            "median=", row["median_interval"],
            "max=", row["max_interval"],
            "status=", row["rhythm_status"],
        )


if __name__ == "__main__":
    main()
