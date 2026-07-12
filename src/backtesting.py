import random
from collections import Counter
from pathlib import Path

from src.frequency_model import DRAW_COUNT, TOTAL_NUMBERS, train_frequency_model
from src.v149_repository_hygiene_engine import head_tail_sample


DEFAULT_BACKTEST_REPORT_PATH = Path("reports") / "backtest_report.md"


def count_matches(ticket: list[int], actual_numbers: list[int]) -> int:
    """
    Count how many predicted numbers matched the actual draw.
    """
    return len(set(ticket) & set(actual_numbers))


def generate_random_ticket() -> list[int]:
    """
    Generate one fair random 6/49 ticket.
    """
    return sorted(random.sample(range(1, TOTAL_NUMBERS + 1), DRAW_COUNT))


def run_rolling_backtest(
    draws: list[dict],
    min_train_size: int = 10,
    recent_window: int = 20,
    random_seed: int = 42,
) -> dict:
    """
    Test the frequency model against future draws.

    For each step:
    - train only on past draws
    - generate a model ticket
    - compare it to the next real draw
    - compare against a random baseline ticket
    """
    if len(draws) <= min_train_size:
        raise ValueError(
            "Not enough historical draws for backtesting. "
            f"Need more than {min_train_size} rows."
        )

    random.seed(random_seed)

    model_match_counts = Counter()
    random_match_counts = Counter()
    model_total_matches = 0
    random_total_matches = 0
    tested_draws = []

    for test_index in range(min_train_size, len(draws)):
        train_draws = draws[:test_index]
        actual_draw = draws[test_index]
        model = train_frequency_model(train_draws, recent_window=recent_window)

        model_ticket = model["recommended_ticket"]
        random_ticket = generate_random_ticket()

        model_matches = count_matches(model_ticket, actual_draw["numbers"])
        random_matches = count_matches(random_ticket, actual_draw["numbers"])

        model_match_counts[model_matches] += 1
        random_match_counts[random_matches] += 1
        model_total_matches += model_matches
        random_total_matches += random_matches

        tested_draws.append(
            {
                "draw_id": actual_draw["draw_id"],
                "date": actual_draw["date"],
                "actual_numbers": actual_draw["numbers"],
                "model_ticket": model_ticket,
                "model_matches": model_matches,
                "random_ticket": random_ticket,
                "random_matches": random_matches,
            }
        )

    test_count = len(tested_draws)

    return {
        "test_count": test_count,
        "min_train_size": min_train_size,
        "recent_window": recent_window,
        "random_seed": random_seed,
        "model_average_matches": model_total_matches / test_count,
        "random_average_matches": random_total_matches / test_count,
        "model_match_distribution": {
            str(matches): model_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "random_match_distribution": {
            str(matches): random_match_counts[matches]
            for matches in range(DRAW_COUNT + 1)
        },
        "tested_draws": tested_draws,
        "conclusion": build_backtest_conclusion(
            model_total_matches / test_count,
            random_total_matches / test_count,
            test_count,
        ),
    }


def build_backtest_conclusion(
    model_average_matches: float,
    random_average_matches: float,
    test_count: int,
) -> str:
    """
    Create a cautious interpretation of the backtest result.
    """
    if test_count < 50:
        sample_note = (
            "The test sample is small, so the result is useful only as a "
            "training check, not as serious evidence."
        )
    else:
        sample_note = (
            "The sample is larger, but lottery results should still be treated "
            "as random unless a strong, stable signal is proven."
        )

    if model_average_matches > random_average_matches:
        comparison = "The frequency model performed better than the random baseline in this run."
    elif model_average_matches < random_average_matches:
        comparison = "The random baseline performed better than the frequency model in this run."
    else:
        comparison = "The frequency model and random baseline were tied in this run."

    return f"{comparison} {sample_note}"


def write_backtest_report(
    backtest_result: dict,
    report_path: Path = DEFAULT_BACKTEST_REPORT_PATH,
) -> Path:
    """
    Write a readable markdown backtest report.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Отчет от историческа проверка",
        "",
        "## Goal",
        "",
        (
            "This report checks whether the historical frequency model performs "
            "better than a random baseline on later draws."
        ),
        "",
        "## Summary",
        "",
        f"- Проверени тиражи: {backtest_result['test_count']}",
        f"- Минимален обучаващ период: {backtest_result['min_train_size']}",
        f"- Последен прозорец: {backtest_result['recent_window']}",
        f"- Случайно семе: {backtest_result['random_seed']}",
        f"- Model average matches: {backtest_result['model_average_matches']:.4f}",
        f"- Random average matches: {backtest_result['random_average_matches']:.4f}",
        "",
        "## Conclusion",
        "",
        backtest_result["conclusion"],
        "",
        "## Match distribution",
        "",
        "| Matches | Model count | Random count |",
        "|---:|---:|---:|",
    ]

    for matches in range(DRAW_COUNT + 1):
        lines.append(
            f"| {matches} | "
            f"{backtest_result['model_match_distribution'][str(matches)]} | "
            f"{backtest_result['random_match_distribution'][str(matches)]} |"
        )

    lines.extend(
        [
            "",
            "## Tested draw sample",
            "",
            "Only the first and last three rows are retained in Markdown. Rerun the backtest to reproduce the complete row-level detail.",
            "",
            "| Draw ID | Date | Actual numbers | Model ticket | Model matches | Random ticket | Random matches |",
            "|:---|:---|:---|:---|---:|:---|---:|",
        ]
    )

    for item in head_tail_sample(backtest_result["tested_draws"]):
        lines.append(
            "| {draw_id} | {date} | {actual} | {model_ticket} | {model_matches} | {random_ticket} | {random_matches} |".format(
                draw_id=item["draw_id"],
                date=item["date"],
                actual=item["actual_numbers"],
                model_ticket=item["model_ticket"],
                model_matches=item["model_matches"],
                random_ticket=item["random_ticket"],
                random_matches=item["random_matches"],
            )
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
