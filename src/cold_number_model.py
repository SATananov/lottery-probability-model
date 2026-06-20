import json
from collections import Counter
from pathlib import Path

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
DEFAULT_COLD_MODEL_PATH = Path("models") / "lottery_cold_model.json"
DEFAULT_COLD_REPORT_PATH = Path("reports") / "cold_model_report.md"
DEFAULT_COLD_BACKTEST_REPORT_PATH = Path("reports") / "cold_backtest_report.md"


def build_cold_number_statistics(draws: list[dict], recent_window: int = 20) -> list[dict]:
    """
    Build statistics for the Cold Numbers / Underrepresented Numbers model.

    The model gives higher scores to numbers that appeared less than expected,
    numbers that have a larger recency gap, and numbers that are also cold in
    the recent window.
    """
    if not draws:
        raise ValueError("Cannot train cold model without historical draws.")

    total_draws = len(draws)
    theoretical_probability = DRAW_COUNT / TOTAL_NUMBERS

    counts = count_number_occurrences(draws)
    recent_counts = calculate_recent_counts(draws, window=recent_window)
    gaps = calculate_recency_gaps(draws)

    actual_recent_window = min(recent_window, total_draws)
    max_gap = max(gaps.values()) if gaps else 1
    if max_gap == 0:
        max_gap = 1

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

        deficit_probability = theoretical_probability - empirical_probability
        recent_deficit_probability = theoretical_probability - recent_probability

        deficit_score = max(deficit_probability, 0) / theoretical_probability
        recent_cold_score = max(recent_deficit_probability, 0) / theoretical_probability
        gap_score = gaps[number] / max_gap

        if deficit_probability > 0:
            cold_status = "UNDER_EXPECTED"
        elif deficit_probability < 0:
            cold_status = "OVER_EXPECTED"
        else:
            cold_status = "EXPECTED"

        statistics.append(
            {
                "number": number,
                "times_drawn": count,
                "empirical_probability": empirical_probability,
                "theoretical_probability": theoretical_probability,
                "deficit_probability": deficit_probability,
                "deficit_score": deficit_score,
                "recent_count": recent_count,
                "recent_probability": recent_probability,
                "recent_cold_score": recent_cold_score,
                "recency_gap": gaps[number],
                "gap_score": gap_score,
                "cold_status": cold_status,
            }
        )

    return statistics


def score_cold_numbers(
    statistics: list[dict],
    deficit_weight: float = 0.50,
    gap_weight: float = 0.30,
    recent_cold_weight: float = 0.20,
) -> list[dict]:
    """
    Score underrepresented numbers.

    Higher score means the number is more underrepresented according to the
    current historical dataset.
    """
    total_weight = deficit_weight + gap_weight + recent_cold_weight
    if total_weight <= 0:
        raise ValueError("Model weights must have a positive total.")

    scored_numbers = []

    for item in statistics:
        score = (
            item["deficit_score"] * deficit_weight
            + item["gap_score"] * gap_weight
            + item["recent_cold_score"] * recent_cold_weight
        ) / total_weight

        scored_item = dict(item)
        scored_item["cold_model_score"] = score
        scored_numbers.append(scored_item)

    return sorted(
        scored_numbers,
        key=lambda item: (
            item["cold_model_score"],
            item["recency_gap"],
            item["deficit_score"],
            -item["number"],
        ),
        reverse=True,
    )


def train_cold_number_model(
    draws: list[dict],
    recent_window: int = 20,
    deficit_weight: float = 0.50,
    gap_weight: float = 0.30,
    recent_cold_weight: float = 0.20,
) -> dict:
    """
    Train the Cold Numbers / Underrepresented Numbers model.
    """
    statistics = build_cold_number_statistics(draws, recent_window=recent_window)
    scored_numbers = score_cold_numbers(
        statistics,
        deficit_weight=deficit_weight,
        gap_weight=gap_weight,
        recent_cold_weight=recent_cold_weight,
    )

    recommended_ticket = sorted(
        item["number"]
        for item in scored_numbers[:DRAW_COUNT]
    )

    return {
        "model_name": "Cold Numbers / Underrepresented Numbers Model",
        "model_version": "1.0",
        "method": (
            "Ranks numbers that are historically below expected frequency, "
            "have larger recency gaps, and are cold in the recent window."
        ),
        "warning": (
            "This is a training baseline, not a guarantee. Lottery draws should "
            "still be treated as random unless a backtest proves a stable signal."
        ),
        "training_draws": len(draws),
        "recent_window": recent_window,
        "weights": {
            "deficit_weight": deficit_weight,
            "gap_weight": gap_weight,
            "recent_cold_weight": recent_cold_weight,
        },
        "recommended_ticket": recommended_ticket,
        "scored_numbers": scored_numbers,
    }


def save_cold_model(
    model: dict,
    model_path: Path = DEFAULT_COLD_MODEL_PATH,
) -> Path:
    """
    Save the trained cold model as JSON.
    """
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(
        json.dumps(model, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return model_path


def load_cold_model(model_path: Path = DEFAULT_COLD_MODEL_PATH) -> dict:
    """
    Load the trained cold model from JSON.
    """
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Cold model file not found: {model_path}")

    return json.loads(model_path.read_text(encoding="utf-8"))


def write_cold_model_report(
    model: dict,
    report_path: Path = DEFAULT_COLD_REPORT_PATH,
) -> Path:
    """
    Write a readable markdown report for the cold model.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Cold Numbers Model Report",
        "",
        "## Purpose",
        "",
        (
            "This report ranks lottery numbers that are underrepresented in the "
            "historical data. The model is useful for training and analysis, but "
            "it does not guarantee future lottery results."
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
        f"- Recommended cold ticket: {model['recommended_ticket']}",
        "",
        "## Weights",
        "",
        f"- Deficit weight: {model['weights']['deficit_weight']}",
        f"- Gap weight: {model['weights']['gap_weight']}",
        f"- Recent cold weight: {model['weights']['recent_cold_weight']}",
        "",
        "## Top underrepresented numbers",
        "",
        "| Rank | Number | Cold score | Times drawn | Empirical probability | Expected probability | Deficit | Recent count | Recency gap | Status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]

    for rank, item in enumerate(model["scored_numbers"][:20], start=1):
        lines.append(
            f"| {rank} | {item['number']} | "
            f"{item['cold_model_score']:.4f} | "
            f"{item['times_drawn']} | "
            f"{item['empirical_probability']:.2%} | "
            f"{item['theoretical_probability']:.2%} | "
            f"{item['deficit_probability']:.2%} | "
            f"{item['recent_count']} | "
            f"{item['recency_gap']} | "
            f"{item['cold_status']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "A high cold score means a number is below expected frequency, "
                "has not appeared recently, or both. This is not proof that the "
                "number is due to appear. It is only a transparent statistical score."
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


def run_cold_backtest(
    draws: list[dict],
    min_train_size: int = 10,
    recent_window: int = 20,
    random_seed: int = 99,
) -> dict:
    """
    Backtest the cold model against a hot frequency model and a random baseline.

    Each test step trains only on previous draws and evaluates on the next draw.
    """
    if len(draws) <= min_train_size:
        raise ValueError(
            "Not enough historical draws for cold backtesting. "
            f"Need more than {min_train_size} rows."
        )

    # Keep the baseline deterministic by reseeding through local predictable tickets.
    # The standard library random state is controlled indirectly by using the
    # existing generator and a fixed import-time seed in this function.
    import random

    random.seed(random_seed)

    cold_match_counts = Counter()
    hot_match_counts = Counter()
    random_match_counts = Counter()
    cold_total_matches = 0
    hot_total_matches = 0
    random_total_matches = 0
    tested_draws = []

    for test_index in range(min_train_size, len(draws)):
        train_draws = draws[:test_index]
        actual_draw = draws[test_index]

        cold_model = train_cold_number_model(train_draws, recent_window=recent_window)
        hot_model = train_frequency_model(train_draws, recent_window=recent_window)

        cold_ticket = cold_model["recommended_ticket"]
        hot_ticket = hot_model["recommended_ticket"]
        random_ticket = generate_random_ticket()

        cold_matches = count_matches(cold_ticket, actual_draw["numbers"])
        hot_matches = count_matches(hot_ticket, actual_draw["numbers"])
        random_matches = count_matches(random_ticket, actual_draw["numbers"])

        cold_match_counts[cold_matches] += 1
        hot_match_counts[hot_matches] += 1
        random_match_counts[random_matches] += 1
        cold_total_matches += cold_matches
        hot_total_matches += hot_matches
        random_total_matches += random_matches

        tested_draws.append(
            {
                "draw_id": actual_draw["draw_id"],
                "date": actual_draw["date"],
                "actual_numbers": actual_draw["numbers"],
                "cold_ticket": cold_ticket,
                "cold_matches": cold_matches,
                "hot_ticket": hot_ticket,
                "hot_matches": hot_matches,
                "random_ticket": random_ticket,
                "random_matches": random_matches,
            }
        )

    test_count = len(tested_draws)
    cold_average = cold_total_matches / test_count
    hot_average = hot_total_matches / test_count
    random_average = random_total_matches / test_count

    return {
        "test_count": test_count,
        "min_train_size": min_train_size,
        "recent_window": recent_window,
        "random_seed": random_seed,
        "cold_average_matches": cold_average,
        "hot_average_matches": hot_average,
        "random_average_matches": random_average,
        "cold_match_distribution": {
            str(matches): cold_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "hot_match_distribution": {
            str(matches): hot_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "random_match_distribution": {
            str(matches): random_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "tested_draws": tested_draws,
        "conclusion": build_cold_backtest_conclusion(
            cold_average,
            hot_average,
            random_average,
            test_count,
        ),
    }


def build_cold_backtest_conclusion(
    cold_average: float,
    hot_average: float,
    random_average: float,
    test_count: int,
) -> str:
    """
    Create a cautious interpretation of the cold model backtest.
    """
    averages = {
        "cold model": cold_average,
        "hot frequency model": hot_average,
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
        f"Cold={cold_average:.4f}, Hot={hot_average:.4f}, Random={random_average:.4f}. "
        f"{sample_note}"
    )


def write_cold_backtest_report(
    backtest_result: dict,
    report_path: Path = DEFAULT_COLD_BACKTEST_REPORT_PATH,
) -> Path:
    """
    Write a markdown report for cold model backtesting.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Cold Numbers Backtest Report",
        "",
        "## Goal",
        "",
        (
            "This report tests whether choosing underrepresented numbers performs "
            "better than the hot frequency model or a random baseline."
        ),
        "",
        "## Summary",
        "",
        f"- Tested draws: {backtest_result['test_count']}",
        f"- Minimum training size: {backtest_result['min_train_size']}",
        f"- Recent window: {backtest_result['recent_window']}",
        f"- Random seed: {backtest_result['random_seed']}",
        f"- Cold model average matches: {backtest_result['cold_average_matches']:.4f}",
        f"- Hot frequency model average matches: {backtest_result['hot_average_matches']:.4f}",
        f"- Random baseline average matches: {backtest_result['random_average_matches']:.4f}",
        "",
        "## Conclusion",
        "",
        backtest_result["conclusion"],
        "",
        "## Match distribution",
        "",
        "| Matches | Cold count | Hot count | Random count |",
        "|---:|---:|---:|---:|",
    ]

    for matches in range(DRAW_COUNT + 1):
        lines.append(
            f"| {matches} | "
            f"{backtest_result['cold_match_distribution'][str(matches)]} | "
            f"{backtest_result['hot_match_distribution'][str(matches)]} | "
            f"{backtest_result['random_match_distribution'][str(matches)]} |"
        )

    lines.extend(
        [
            "",
            "## Tested draws",
            "",
            "| Draw ID | Date | Actual numbers | Cold ticket | Cold matches | Hot ticket | Hot matches | Random ticket | Random matches |",
            "|:---|:---|:---|:---|---:|:---|---:|:---|---:|",
        ]
    )

    for item in backtest_result["tested_draws"]:
        lines.append(
            "| {draw_id} | {date} | {actual} | {cold_ticket} | {cold_matches} | {hot_ticket} | {hot_matches} | {random_ticket} | {random_matches} |".format(
                draw_id=item["draw_id"],
                date=item["date"],
                actual=item["actual_numbers"],
                cold_ticket=item["cold_ticket"],
                cold_matches=item["cold_matches"],
                hot_ticket=item["hot_ticket"],
                hot_matches=item["hot_matches"],
                random_ticket=item["random_ticket"],
                random_matches=item["random_matches"],
            )
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path