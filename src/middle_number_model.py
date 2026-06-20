import json
import math
import random
from collections import Counter
from pathlib import Path

from src.cold_number_model import train_cold_number_model
from src.frequency_model import (
    DRAW_COUNT,
    TOTAL_NUMBERS,
    calculate_recency_gaps,
    calculate_recent_counts,
    count_number_occurrences,
    load_draws,
    train_frequency_model,
)
from src.generator import generate_random_combination
from src.simulation import count_matches


DEFAULT_DATA_PATH = Path("data") / "historical_draws.csv"
DEFAULT_MIDDLE_MODEL_PATH = Path("models") / "lottery_middle_model.json"
DEFAULT_MIDDLE_REPORT_PATH = Path("reports") / "middle_model_report.md"
DEFAULT_MIDDLE_BACKTEST_REPORT_PATH = Path("reports") / "middle_backtest_report.md"


def _safe_balance_score(value: float, expected: float) -> float:
    """
    Convert distance from the expected value into a 0-1 balance score.

    1.0 means the value is exactly at the expected point.
    0.0 means it is at least one expected unit away.
    """
    if expected <= 0:
        return 0.0

    relative_distance = abs(value - expected) / expected
    return max(0.0, 1.0 - relative_distance)


def build_middle_number_statistics(draws: list[dict], recent_window: int = 20) -> list[dict]:
    """
    Build statistics for the Middle / Balanced Numbers model.

    This model gives higher scores to numbers whose historical behavior is
    closest to the expected fair 6/49 probability. It avoids the extremes:
    very hot numbers and very cold numbers.
    """
    if not draws:
        raise ValueError("Cannot train middle model without historical draws.")

    total_draws = len(draws)
    theoretical_probability = DRAW_COUNT / TOTAL_NUMBERS
    expected_count = total_draws * theoretical_probability

    counts = count_number_occurrences(draws)
    recent_counts = calculate_recent_counts(draws, window=recent_window)
    gaps = calculate_recency_gaps(draws)

    actual_recent_window = min(recent_window, total_draws)
    expected_gap = (1 - theoretical_probability) / theoretical_probability

    variance = total_draws * theoretical_probability * (1 - theoretical_probability)
    standard_deviation = math.sqrt(variance) if variance > 0 else 0

    statistics = []

    for number in range(1, TOTAL_NUMBERS + 1):
        count = counts[number]
        recent_count = recent_counts[number]

        empirical_probability = count / total_draws
        recent_probability = (
            recent_count / actual_recent_window
            if actual_recent_window > 0
            else 0
        )

        difference = empirical_probability - theoretical_probability
        absolute_difference = abs(difference)
        z_score = (
            (count - expected_count) / standard_deviation
            if standard_deviation > 0
            else 0
        )

        empirical_balance_score = _safe_balance_score(
            empirical_probability,
            theoretical_probability,
        )
        recent_balance_score = _safe_balance_score(
            recent_probability,
            theoretical_probability,
        )
        gap_balance_score = _safe_balance_score(gaps[number], expected_gap)

        if abs(z_score) <= 1:
            middle_status = "MIDDLE"
        elif z_score > 1:
            middle_status = "ABOVE_MIDDLE"
        else:
            middle_status = "BELOW_MIDDLE"

        statistics.append(
            {
                "number": number,
                "times_drawn": count,
                "recent_times_drawn": recent_count,
                "recency_gap": gaps[number],
                "empirical_probability": empirical_probability,
                "recent_probability": recent_probability,
                "theoretical_probability": theoretical_probability,
                "difference_from_theoretical": difference,
                "absolute_difference_from_theoretical": absolute_difference,
                "z_score": z_score,
                "expected_gap": expected_gap,
                "empirical_balance_score": empirical_balance_score,
                "recent_balance_score": recent_balance_score,
                "gap_balance_score": gap_balance_score,
                "middle_status": middle_status,
            }
        )

    return statistics


def score_middle_numbers(
    statistics: list[dict],
    closeness_weight: float = 0.60,
    gap_balance_weight: float = 0.25,
    recent_balance_weight: float = 0.15,
) -> list[dict]:
    """
    Score numbers that are closest to the expected fair behavior.
    """
    total_weight = closeness_weight + gap_balance_weight + recent_balance_weight
    if total_weight <= 0:
        raise ValueError("Model weights must have a positive total.")

    scored_numbers = []

    for item in statistics:
        score = (
            item["empirical_balance_score"] * closeness_weight
            + item["gap_balance_score"] * gap_balance_weight
            + item["recent_balance_score"] * recent_balance_weight
        ) / total_weight

        scored_item = dict(item)
        scored_item["middle_model_score"] = score
        scored_numbers.append(scored_item)

    return sorted(
        scored_numbers,
        key=lambda item: (
            -item["middle_model_score"],
            item["absolute_difference_from_theoretical"],
            abs(item["z_score"]),
            item["number"],
        ),
    )


def train_middle_number_model(
    draws: list[dict],
    recent_window: int = 20,
    closeness_weight: float = 0.60,
    gap_balance_weight: float = 0.25,
    recent_balance_weight: float = 0.15,
) -> dict:
    """
    Train the Middle / Balanced Numbers model.
    """
    statistics = build_middle_number_statistics(draws, recent_window=recent_window)
    scored_numbers = score_middle_numbers(
        statistics,
        closeness_weight=closeness_weight,
        gap_balance_weight=gap_balance_weight,
        recent_balance_weight=recent_balance_weight,
    )

    recommended_ticket = sorted(
        item["number"]
        for item in scored_numbers[:DRAW_COUNT]
    )

    return {
        "model_name": "Middle / Balanced Numbers Model",
        "model_version": "1.0",
        "method": (
            "Ranks numbers whose historical frequency, recent frequency, and "
            "recency gap are closest to the expected fair 6/49 behavior."
        ),
        "warning": (
            "This is a statistical training baseline. It identifies numbers "
            "near the historical middle, but it does not guarantee future lottery results."
        ),
        "training_draws": len(draws),
        "recent_window": min(recent_window, len(draws)),
        "weights": {
            "closeness_weight": closeness_weight,
            "gap_balance_weight": gap_balance_weight,
            "recent_balance_weight": recent_balance_weight,
        },
        "recommended_ticket": recommended_ticket,
        "scored_numbers": scored_numbers,
    }


def save_middle_model(
    model: dict,
    model_path: Path = DEFAULT_MIDDLE_MODEL_PATH,
) -> Path:
    """
    Save the trained middle model as JSON.
    """
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(
        json.dumps(model, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return model_path


def load_middle_model(model_path: Path = DEFAULT_MIDDLE_MODEL_PATH) -> dict:
    """
    Load the trained middle model from JSON.
    """
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Middle model file not found: {model_path}")

    return json.loads(model_path.read_text(encoding="utf-8"))


def write_middle_model_report(
    model: dict,
    report_path: Path = DEFAULT_MIDDLE_REPORT_PATH,
) -> Path:
    """
    Write a readable markdown report for the middle model.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Middle / Balanced Numbers Model Report",
        "",
        "## Purpose",
        "",
        (
            "This report ranks numbers that are closest to the expected fair "
            "6/49 behavior. The model avoids extreme hot and cold numbers."
        ),
        "",
        "## Model method",
        "",
        model["method"],
        "",
        "## Training summary",
        "",
        f"- Training draws: {model['training_draws']}",
        f"- Recent window: {model['recent_window']}",
        f"- Recommended middle ticket: {model['recommended_ticket']}",
        "",
        "## Weights",
        "",
        f"- Closeness to expected frequency: {model['weights']['closeness_weight']}",
        f"- Gap balance: {model['weights']['gap_balance_weight']}",
        f"- Recent balance: {model['weights']['recent_balance_weight']}",
        "",
        "## Top balanced numbers",
        "",
        "| Rank | Number | Middle score | Times drawn | Empirical probability | Expected probability | Difference | Z-score | Gap | Status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]

    for rank, item in enumerate(model["scored_numbers"][:20], start=1):
        lines.append(
            f"| {rank} | {item['number']} | "
            f"{item['middle_model_score']:.4f} | "
            f"{item['times_drawn']} | "
            f"{item['empirical_probability']:.2%} | "
            f"{item['theoretical_probability']:.2%} | "
            f"{item['difference_from_theoretical']:.2%} | "
            f"{item['z_score']:.2f} | "
            f"{item['recency_gap']} | "
            f"{item['middle_status']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "A high middle score means a number is close to the expected "
                "average statistical behavior. This is not proof that the number "
                "will appear next; it is only a transparent balancing strategy."
            ),
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def generate_random_ticket() -> list[int]:
    """
    Generate a random 6/49 ticket for baseline comparison.
    """
    return generate_random_combination()


def run_middle_backtest(
    draws: list[dict],
    min_train_size: int = 10,
    recent_window: int = 20,
    random_seed: int = 123,
) -> dict:
    """
    Backtest the middle model against hot, cold, and random baselines.

    Each test step trains only on previous draws and evaluates on the next draw.
    """
    if len(draws) <= min_train_size:
        raise ValueError(
            "Not enough historical draws for middle backtesting. "
            f"Need more than {min_train_size} rows."
        )

    random.seed(random_seed)

    middle_match_counts = Counter()
    hot_match_counts = Counter()
    cold_match_counts = Counter()
    random_match_counts = Counter()

    middle_total_matches = 0
    hot_total_matches = 0
    cold_total_matches = 0
    random_total_matches = 0
    tested_draws = []

    for test_index in range(min_train_size, len(draws)):
        train_draws = draws[:test_index]
        actual_draw = draws[test_index]

        middle_model = train_middle_number_model(train_draws, recent_window=recent_window)
        hot_model = train_frequency_model(train_draws, recent_window=recent_window)
        cold_model = train_cold_number_model(train_draws, recent_window=recent_window)

        middle_ticket = middle_model["recommended_ticket"]
        hot_ticket = hot_model["recommended_ticket"]
        cold_ticket = cold_model["recommended_ticket"]
        random_ticket = generate_random_ticket()

        middle_matches = count_matches(middle_ticket, actual_draw["numbers"])
        hot_matches = count_matches(hot_ticket, actual_draw["numbers"])
        cold_matches = count_matches(cold_ticket, actual_draw["numbers"])
        random_matches = count_matches(random_ticket, actual_draw["numbers"])

        middle_match_counts[middle_matches] += 1
        hot_match_counts[hot_matches] += 1
        cold_match_counts[cold_matches] += 1
        random_match_counts[random_matches] += 1

        middle_total_matches += middle_matches
        hot_total_matches += hot_matches
        cold_total_matches += cold_matches
        random_total_matches += random_matches

        tested_draws.append(
            {
                "draw_id": actual_draw["draw_id"],
                "date": actual_draw["date"],
                "actual_numbers": actual_draw["numbers"],
                "middle_ticket": middle_ticket,
                "middle_matches": middle_matches,
                "hot_ticket": hot_ticket,
                "hot_matches": hot_matches,
                "cold_ticket": cold_ticket,
                "cold_matches": cold_matches,
                "random_ticket": random_ticket,
                "random_matches": random_matches,
            }
        )

    test_count = len(tested_draws)
    middle_average = middle_total_matches / test_count
    hot_average = hot_total_matches / test_count
    cold_average = cold_total_matches / test_count
    random_average = random_total_matches / test_count

    return {
        "test_count": test_count,
        "min_train_size": min_train_size,
        "recent_window": recent_window,
        "random_seed": random_seed,
        "middle_average_matches": middle_average,
        "hot_average_matches": hot_average,
        "cold_average_matches": cold_average,
        "random_average_matches": random_average,
        "middle_match_distribution": {
            str(matches): middle_match_counts[matches]
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
        "random_match_distribution": {
            str(matches): random_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "tested_draws": tested_draws,
        "conclusion": build_middle_backtest_conclusion(
            middle_average,
            hot_average,
            cold_average,
            random_average,
            test_count,
        ),
    }


def build_middle_backtest_conclusion(
    middle_average: float,
    hot_average: float,
    cold_average: float,
    random_average: float,
    test_count: int,
) -> str:
    """
    Create a cautious interpretation of the middle model backtest.
    """
    averages = {
        "middle model": middle_average,
        "hot frequency model": hot_average,
        "cold model": cold_average,
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
        f"Middle={middle_average:.4f}, Hot={hot_average:.4f}, "
        f"Cold={cold_average:.4f}, Random={random_average:.4f}. "
        f"{sample_note}"
    )


def write_middle_backtest_report(
    backtest_result: dict,
    report_path: Path = DEFAULT_MIDDLE_BACKTEST_REPORT_PATH,
) -> Path:
    """
    Write a readable markdown backtest report for the middle model.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Middle Model Backtest Report",
        "",
        "## Goal",
        "",
        (
            "This report checks whether the middle/balanced model performs "
            "better than hot, cold, and random baselines on later draws."
        ),
        "",
        "## Summary",
        "",
        f"- Tested draws: {backtest_result['test_count']}",
        f"- Minimum training size: {backtest_result['min_train_size']}",
        f"- Recent window: {backtest_result['recent_window']}",
        f"- Random seed: {backtest_result['random_seed']}",
        f"- Middle average matches: {backtest_result['middle_average_matches']:.4f}",
        f"- Hot average matches: {backtest_result['hot_average_matches']:.4f}",
        f"- Cold average matches: {backtest_result['cold_average_matches']:.4f}",
        f"- Random average matches: {backtest_result['random_average_matches']:.4f}",
        "",
        "## Conclusion",
        "",
        backtest_result["conclusion"],
        "",
        "## Match distribution",
        "",
        "| Matches | Middle count | Hot count | Cold count | Random count |",
        "|---:|---:|---:|---:|---:|",
    ]

    for matches in range(DRAW_COUNT + 1):
        lines.append(
            f"| {matches} | "
            f"{backtest_result['middle_match_distribution'][str(matches)]} | "
            f"{backtest_result['hot_match_distribution'][str(matches)]} | "
            f"{backtest_result['cold_match_distribution'][str(matches)]} | "
            f"{backtest_result['random_match_distribution'][str(matches)]} |"
        )

    lines.extend(
        [
            "",
            "## Tested draws",
            "",
            "| Draw ID | Date | Actual numbers | Middle ticket | Middle matches | Hot ticket | Hot matches | Cold ticket | Cold matches | Random ticket | Random matches |",
            "|:---|:---|:---|:---|---:|:---|---:|:---|---:|:---|---:|",
        ]
    )

    for item in backtest_result["tested_draws"]:
        lines.append(
            "| {draw_id} | {date} | {actual} | {middle_ticket} | {middle_matches} | {hot_ticket} | {hot_matches} | {cold_ticket} | {cold_matches} | {random_ticket} | {random_matches} |".format(
                draw_id=item["draw_id"],
                date=item["date"],
                actual=item["actual_numbers"],
                middle_ticket=item["middle_ticket"],
                middle_matches=item["middle_matches"],
                hot_ticket=item["hot_ticket"],
                hot_matches=item["hot_matches"],
                cold_ticket=item["cold_ticket"],
                cold_matches=item["cold_matches"],
                random_ticket=item["random_ticket"],
                random_matches=item["random_matches"],
            )
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path

