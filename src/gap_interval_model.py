import json
import random
from collections import Counter
from pathlib import Path

from src.cold_number_model import train_cold_number_model
from src.frequency_model import (
    DRAW_COUNT,
    TOTAL_NUMBERS,
    calculate_recency_gaps,
    count_number_occurrences,
    load_draws,
    train_frequency_model,
)
from src.generator import generate_random_combination
from src.middle_number_model import train_middle_number_model
from src.simulation import count_matches
from src.v149_repository_hygiene_engine import head_tail_sample


DEFAULT_DATA_PATH = Path("data") / "historical_draws.csv"
DEFAULT_GAP_MODEL_PATH = Path("models") / "lottery_gap_model.json"
DEFAULT_GAP_REPORT_PATH = Path("reports") / "gap_model_report.md"
DEFAULT_GAP_BACKTEST_REPORT_PATH = Path("reports") / "gap_backtest_report.md"


BASELINE_NEXT_DRAW_PROBABILITY = DRAW_COUNT / TOTAL_NUMBERS


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """
    Keep a value inside a safe range.
    """
    return max(minimum, min(maximum, value))


def build_appearance_positions(draws: list[dict]) -> dict[int, list[int]]:
    """
    Build 0-based draw positions where each number appeared.
    """
    positions = {number: [] for number in range(1, TOTAL_NUMBERS + 1)}

    for draw_index, draw in enumerate(draws):
        for number in draw["numbers"]:
            positions[number].append(draw_index)

    return positions


def calculate_intervals(positions: list[int]) -> list[int]:
    """
    Calculate distances between consecutive appearances.

    Example: positions [2, 9, 17] -> intervals [7, 8].
    """
    if len(positions) < 2:
        return []

    return [
        current_position - previous_position
        for previous_position, current_position in zip(positions, positions[1:])
    ]


def estimate_interval_hazard_probability(
    intervals: list[int],
    next_interval_distance: int,
    baseline_probability: float = BASELINE_NEXT_DRAW_PROBABILITY,
    smoothing_strength: float = 12.0,
) -> tuple[float, int, int]:
    """
    Estimate probability that a number appears in the next draw based on intervals.

    If a number last appeared G draws ago, appearing in the next draw would mean
    the new interval distance is G + 1. This function estimates the historical
    hazard:

    P(interval == G + 1 | interval >= G + 1)

    Smoothing keeps the estimate stable when the dataset is small.
    """
    if next_interval_distance <= 0:
        next_interval_distance = 1

    if not intervals:
        return baseline_probability, 0, 0

    at_risk_count = sum(1 for interval in intervals if interval >= next_interval_distance)
    hit_count = sum(1 for interval in intervals if interval == next_interval_distance)

    if at_risk_count == 0:
        return baseline_probability, 0, 0

    probability = (
        hit_count + baseline_probability * smoothing_strength
    ) / (at_risk_count + smoothing_strength)

    return probability, at_risk_count, hit_count


def build_gap_interval_statistics(draws: list[dict]) -> list[dict]:
    """
    Build interval and next-draw probability statistics for every number.
    """
    if not draws:
        raise ValueError("Cannot train gap model without historical draws.")

    total_draws = len(draws)
    counts = count_number_occurrences(draws)
    recency_gaps = calculate_recency_gaps(draws)
    positions_by_number = build_appearance_positions(draws)

    baseline_probability = BASELINE_NEXT_DRAW_PROBABILITY
    expected_interval = 1 / baseline_probability

    statistics = []

    for number in range(1, TOTAL_NUMBERS + 1):
        positions = positions_by_number[number]
        intervals = calculate_intervals(positions)
        appearances = len(positions)
        empirical_probability = appearances / total_draws

        current_gap = recency_gaps[number]
        next_interval_distance = current_gap + 1

        if intervals:
            average_interval = sum(intervals) / len(intervals)
            sorted_intervals = sorted(intervals)
            middle_index = len(sorted_intervals) // 2
            if len(sorted_intervals) % 2 == 1:
                median_interval = float(sorted_intervals[middle_index])
            else:
                median_interval = (
                    sorted_intervals[middle_index - 1] + sorted_intervals[middle_index]
                ) / 2
            min_interval = min(intervals)
            max_interval = max(intervals)
        else:
            average_interval = expected_interval
            median_interval = expected_interval
            min_interval = None
            max_interval = None

        gap_ratio = (
            next_interval_distance / average_interval
            if average_interval > 0
            else 1.0
        )

        interval_probability, at_risk_count, hit_count = estimate_interval_hazard_probability(
            intervals,
            next_interval_distance,
            baseline_probability=baseline_probability,
        )

        gap_pressure_multiplier = _clamp(gap_ratio, 0.50, 1.80)
        gap_pressure_probability = _clamp(
            baseline_probability * gap_pressure_multiplier,
            0.0,
            0.35,
        )

        combined_next_probability = (
            interval_probability * 0.45
            + gap_pressure_probability * 0.25
            + empirical_probability * 0.20
            + baseline_probability * 0.10
        )
        combined_next_probability = _clamp(combined_next_probability, 0.0, 0.50)

        if appearances < 2:
            interval_status = "LIMITED_HISTORY"
        elif gap_ratio >= 1.70:
            interval_status = "STRONGLY_OVERDUE"
        elif gap_ratio >= 1.30:
            interval_status = "OVERDUE"
        elif gap_ratio <= 0.60:
            interval_status = "RECENT"
        else:
            interval_status = "NORMAL_INTERVAL"

        statistics.append(
            {
                "number": number,
                "appearances": appearances,
                "empirical_probability": empirical_probability,
                "baseline_probability": baseline_probability,
                "current_gap": current_gap,
                "next_interval_distance": next_interval_distance,
                "average_interval": average_interval,
                "median_interval": median_interval,
                "min_interval": min_interval,
                "max_interval": max_interval,
                "gap_ratio": gap_ratio,
                "interval_hazard_probability": interval_probability,
                "interval_at_risk_count": at_risk_count,
                "interval_hit_count": hit_count,
                "gap_pressure_probability": gap_pressure_probability,
                "combined_next_probability": combined_next_probability,
                "interval_status": interval_status,
            }
        )

    return statistics


def score_gap_interval_numbers(statistics: list[dict]) -> list[dict]:
    """
    Sort numbers by the combined next-draw probability estimate.
    """
    return sorted(
        statistics,
        key=lambda item: (
            -item["combined_next_probability"],
            -item["gap_ratio"],
            -item["current_gap"],
            -item["appearances"],
            item["number"],
        ),
    )


def train_gap_interval_model(draws: list[dict]) -> dict:
    """
    Train the Gap / Interval Next-Draw Probability model.
    """
    statistics = build_gap_interval_statistics(draws)
    scored_numbers = score_gap_interval_numbers(statistics)

    recommended_ticket = sorted(
        item["number"]
        for item in scored_numbers[:DRAW_COUNT]
    )

    return {
        "model_name": "Gap / Interval Next-Draw Probability Model",
        "model_version": "1.0",
        "method": (
            "Ranks numbers by recurrence intervals. For each number, the model "
            "compares the current gap since its last appearance with its average "
            "historical interval, estimates an interval hazard probability, and "
            "combines it with the fair 6/49 baseline and empirical frequency."
        ),
        "warning": (
            "The fair mathematical chance for any single number to appear in the "
            "next 6/49 draw is still 6/49. This model is a statistical training "
            "estimate based on historical intervals, not a guarantee."
        ),
        "training_draws": len(draws),
        "baseline_next_draw_probability": BASELINE_NEXT_DRAW_PROBABILITY,
        "recommended_ticket": recommended_ticket,
        "scored_numbers": scored_numbers,
    }


def save_gap_model(
    model: dict,
    model_path: Path = DEFAULT_GAP_MODEL_PATH,
) -> Path:
    """
    Save the trained gap model as JSON.
    """
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(
        json.dumps(model, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return model_path


def load_gap_model(model_path: Path = DEFAULT_GAP_MODEL_PATH) -> dict:
    """
    Load the trained gap model from JSON.
    """
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Gap model file not found: {model_path}")

    return json.loads(model_path.read_text(encoding="utf-8"))


def write_gap_model_report(
    model: dict,
    report_path: Path = DEFAULT_GAP_REPORT_PATH,
) -> Path:
    """
    Write a readable markdown report for the gap interval model.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Gap / Interval Next-Draw Probability Model Report",
        "",
        "## Purpose",
        "",
        (
            "This report estimates which numbers have the strongest next-draw "
            "score based on historical recurrence intervals."
        ),
        "",
        "## Model method",
        "",
        model["method"],
        "",
        "## Important warning",
        "",
        model["warning"],
        "",
        "## Training summary",
        "",
        f"- Training draws: {model['training_draws']}",
        f"- Baseline next-draw probability per number: {model['baseline_next_draw_probability']:.2%}",
        f"- Recommended gap ticket: {model['recommended_ticket']}",
        "",
        "## Top next-draw probability numbers",
        "",
        "| Rank | Number | Combined probability | Baseline | Interval hazard | Empirical | Current gap | Avg interval | Gap ratio | Cases | Hits | Status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]

    for rank, item in enumerate(model["scored_numbers"][:20], start=1):
        lines.append(
            f"| {rank} | {item['number']} | "
            f"{item['combined_next_probability']:.2%} | "
            f"{item['baseline_probability']:.2%} | "
            f"{item['interval_hazard_probability']:.2%} | "
            f"{item['empirical_probability']:.2%} | "
            f"{item['current_gap']} | "
            f"{item['average_interval']:.2f} | "
            f"{item['gap_ratio']:.2f} | "
            f"{item['interval_at_risk_count']} | "
            f"{item['interval_hit_count']} | "
            f"{item['interval_status']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "A high combined probability means that the number is interesting "
                "according to its historical interval rhythm. It does not mean the "
                "number is guaranteed to appear in the next draw."
            ),
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_gap_backtest(
    draws: list[dict],
    min_train_size: int = 10,
    random_seed: int = 456,
) -> dict:
    """
    Backtest the gap model against hot, cold, middle, and random baselines.
    """
    if len(draws) <= min_train_size:
        raise ValueError(
            "Not enough historical draws for gap backtesting. "
            f"Need more than {min_train_size} rows."
        )

    random.seed(random_seed)

    gap_match_counts = Counter()
    hot_match_counts = Counter()
    cold_match_counts = Counter()
    middle_match_counts = Counter()
    random_match_counts = Counter()

    gap_total_matches = 0
    hot_total_matches = 0
    cold_total_matches = 0
    middle_total_matches = 0
    random_total_matches = 0
    tested_draws = []

    for test_index in range(min_train_size, len(draws)):
        train_draws = draws[:test_index]
        actual_draw = draws[test_index]

        gap_model = train_gap_interval_model(train_draws)
        hot_model = train_frequency_model(train_draws)
        cold_model = train_cold_number_model(train_draws)
        middle_model = train_middle_number_model(train_draws)

        gap_ticket = gap_model["recommended_ticket"]
        hot_ticket = hot_model["recommended_ticket"]
        cold_ticket = cold_model["recommended_ticket"]
        middle_ticket = middle_model["recommended_ticket"]
        random_ticket = generate_random_combination()

        gap_matches = count_matches(gap_ticket, actual_draw["numbers"])
        hot_matches = count_matches(hot_ticket, actual_draw["numbers"])
        cold_matches = count_matches(cold_ticket, actual_draw["numbers"])
        middle_matches = count_matches(middle_ticket, actual_draw["numbers"])
        random_matches = count_matches(random_ticket, actual_draw["numbers"])

        gap_match_counts[gap_matches] += 1
        hot_match_counts[hot_matches] += 1
        cold_match_counts[cold_matches] += 1
        middle_match_counts[middle_matches] += 1
        random_match_counts[random_matches] += 1

        gap_total_matches += gap_matches
        hot_total_matches += hot_matches
        cold_total_matches += cold_matches
        middle_total_matches += middle_matches
        random_total_matches += random_matches

        tested_draws.append(
            {
                "draw_id": actual_draw["draw_id"],
                "date": actual_draw["date"],
                "actual_numbers": actual_draw["numbers"],
                "gap_ticket": gap_ticket,
                "gap_matches": gap_matches,
                "hot_ticket": hot_ticket,
                "hot_matches": hot_matches,
                "cold_ticket": cold_ticket,
                "cold_matches": cold_matches,
                "middle_ticket": middle_ticket,
                "middle_matches": middle_matches,
                "random_ticket": random_ticket,
                "random_matches": random_matches,
            }
        )

    test_count = len(tested_draws)
    gap_average = gap_total_matches / test_count
    hot_average = hot_total_matches / test_count
    cold_average = cold_total_matches / test_count
    middle_average = middle_total_matches / test_count
    random_average = random_total_matches / test_count

    return {
        "test_count": test_count,
        "min_train_size": min_train_size,
        "random_seed": random_seed,
        "gap_average_matches": gap_average,
        "hot_average_matches": hot_average,
        "cold_average_matches": cold_average,
        "middle_average_matches": middle_average,
        "random_average_matches": random_average,
        "gap_match_distribution": {
            str(matches): gap_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "hot_match_distribution": {
            str(matches): hot_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "cold_match_distribution": {
            str(matches): cold_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "middle_match_distribution": {
            str(matches): middle_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "random_match_distribution": {
            str(matches): random_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "tested_draws": tested_draws,
        "conclusion": build_gap_backtest_conclusion(
            gap_average,
            hot_average,
            cold_average,
            middle_average,
            random_average,
            test_count,
        ),
    }


def build_gap_backtest_conclusion(
    gap_average: float,
    hot_average: float,
    cold_average: float,
    middle_average: float,
    random_average: float,
    test_count: int,
) -> str:
    """
    Create a cautious interpretation of the gap model backtest.
    """
    averages = {
        "gap interval model": gap_average,
        "hot frequency model": hot_average,
        "cold model": cold_average,
        "middle model": middle_average,
        "random baseline": random_average,
    }
    winner = max(averages, key=averages.get)

    if test_count < 50:
        sample_note = (
            "The test sample is small, so this result is only a training check."
        )
    else:
        sample_note = (
            "The sample is larger, but the result still needs cautious interpretation."
        )

    return (
        f"Best average in this run: {winner}. "
        f"Gap={gap_average:.4f}, Hot={hot_average:.4f}, "
        f"Cold={cold_average:.4f}, Middle={middle_average:.4f}, "
        f"Random={random_average:.4f}. {sample_note}"
    )


def write_gap_backtest_report(
    backtest_result: dict,
    report_path: Path = DEFAULT_GAP_BACKTEST_REPORT_PATH,
) -> Path:
    """
    Write a readable markdown backtest report for the gap model.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Gap / Interval Model Backtest Report",
        "",
        "## Goal",
        "",
        (
            "This report checks whether the gap/interval probability model "
            "performs better than hot, cold, middle, and random baselines."
        ),
        "",
        "## Summary",
        "",
        f"- Проверени тиражи: {backtest_result['test_count']}",
        f"- Минимален обучаващ период: {backtest_result['min_train_size']}",
        f"- Случайно семе: {backtest_result['random_seed']}",
        f"- Gap average matches: {backtest_result['gap_average_matches']:.4f}",
        f"- Hot average matches: {backtest_result['hot_average_matches']:.4f}",
        f"- Cold average matches: {backtest_result['cold_average_matches']:.4f}",
        f"- Middle average matches: {backtest_result['middle_average_matches']:.4f}",
        f"- Random average matches: {backtest_result['random_average_matches']:.4f}",
        "",
        "## Conclusion",
        "",
        backtest_result["conclusion"],
        "",
        "## Match distribution",
        "",
        "| Matches | Gap count | Hot count | Cold count | Middle count | Random count |",
        "|---:|---:|---:|---:|---:|---:|",
    ]

    for matches in range(DRAW_COUNT + 1):
        lines.append(
            f"| {matches} | "
            f"{backtest_result['gap_match_distribution'][str(matches)]} | "
            f"{backtest_result['hot_match_distribution'][str(matches)]} | "
            f"{backtest_result['cold_match_distribution'][str(matches)]} | "
            f"{backtest_result['middle_match_distribution'][str(matches)]} | "
            f"{backtest_result['random_match_distribution'][str(matches)]} |"
        )

    lines.extend(
        [
            "",
            "## Tested draw sample",
            "",
            "Only the first and last three rows are retained in Markdown. Rerun the backtest to reproduce the complete row-level detail.",
            "",
            "| Draw ID | Date | Actual numbers | Gap ticket | Gap matches | Hot ticket | Hot matches | Cold ticket | Cold matches | Middle ticket | Middle matches | Random ticket | Random matches |",
            "|:---|:---|:---|:---|---:|:---|---:|:---|---:|:---|---:|:---|---:|",
        ]
    )

    for item in head_tail_sample(backtest_result["tested_draws"]):
        lines.append(
            "| {draw_id} | {date} | {actual} | {gap_ticket} | {gap_matches} | {hot_ticket} | {hot_matches} | {cold_ticket} | {cold_matches} | {middle_ticket} | {middle_matches} | {random_ticket} | {random_matches} |".format(
                draw_id=item["draw_id"],
                date=item["date"],
                actual=item["actual_numbers"],
                gap_ticket=item["gap_ticket"],
                gap_matches=item["gap_matches"],
                hot_ticket=item["hot_ticket"],
                hot_matches=item["hot_matches"],
                cold_ticket=item["cold_ticket"],
                cold_matches=item["cold_matches"],
                middle_ticket=item["middle_ticket"],
                middle_matches=item["middle_matches"],
                random_ticket=item["random_ticket"],
                random_matches=item["random_matches"],
            )
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
