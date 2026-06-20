import csv
from collections import Counter
from itertools import combinations
from pathlib import Path


TOTAL_NUMBERS = 49
DRAW_COUNT = 6
NUMBER_COLUMNS = ["n1", "n2", "n3", "n4", "n5", "n6"]
DEFAULT_DATA_PATH = Path("data") / "historical_draws.csv"
DEFAULT_REPORT_PATH = Path("reports") / "historical_report.md"


def validate_draw_numbers(numbers: list[int]) -> None:
    """
    Validate one historical 6/49 draw.
    """
    if len(numbers) != DRAW_COUNT:
        raise ValueError("Each draw must contain exactly 6 numbers.")

    if len(set(numbers)) != DRAW_COUNT:
        raise ValueError(f"Draw contains duplicate numbers: {numbers}")

    invalid_numbers = [
        number for number in numbers
        if number < 1 or number > TOTAL_NUMBERS
    ]

    if invalid_numbers:
        raise ValueError(f"Draw contains invalid numbers: {invalid_numbers}")


def load_historical_draws(csv_path: Path = DEFAULT_DATA_PATH) -> list[dict]:
    """
    Load historical lottery draws from a CSV file.

    Expected columns:
    draw_id,date,n1,n2,n3,n4,n5,n6
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Historical data file not found: {csv_path}")

    draws = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"draw_id", "date", *NUMBER_COLUMNS}

        if reader.fieldnames is None:
            raise ValueError("Historical data file is empty.")

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(f"Missing columns in historical CSV: {missing_columns}")

        for row_index, row in enumerate(reader, start=2):
            try:
                numbers = [int(row[column]) for column in NUMBER_COLUMNS]
            except ValueError as error:
                raise ValueError(
                    f"Invalid number value on CSV row {row_index}: {row}"
                ) from error

            validate_draw_numbers(numbers)

            draws.append(
                {
                    "draw_id": row["draw_id"],
                    "date": row["date"],
                    "numbers": sorted(numbers),
                }
            )

    return draws


def calculate_number_frequencies(draws: list[dict]) -> dict[int, int]:
    """
    Count how many times each number appeared in the historical draws.
    """
    counter = Counter()

    for draw in draws:
        counter.update(draw["numbers"])

    return {number: counter.get(number, 0) for number in range(1, TOTAL_NUMBERS + 1)}


def get_hot_numbers(frequencies: dict[int, int], limit: int = 10) -> list[tuple[int, int]]:
    """
    Return the most frequent numbers.
    """
    return sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))[:limit]


def get_cold_numbers(frequencies: dict[int, int], limit: int = 10) -> list[tuple[int, int]]:
    """
    Return the least frequent numbers.
    """
    return sorted(frequencies.items(), key=lambda item: (item[1], item[0]))[:limit]


def calculate_recency_gaps(draws: list[dict]) -> dict[int, int]:
    """
    Count how many draws have passed since each number last appeared.

    A gap of 0 means the number appeared in the latest draw.
    """
    gaps = {}

    for number in range(1, TOTAL_NUMBERS + 1):
        gap = len(draws)

        for reversed_index, draw in enumerate(reversed(draws)):
            if number in draw["numbers"]:
                gap = reversed_index
                break

        gaps[number] = gap

    return gaps


def get_overdue_numbers(gaps: dict[int, int], limit: int = 10) -> list[tuple[int, int]]:
    """
    Return numbers that have not appeared for the longest time.
    """
    return sorted(gaps.items(), key=lambda item: (-item[1], item[0]))[:limit]


def calculate_pair_frequencies(draws: list[dict], limit: int = 10) -> list[tuple[tuple[int, int], int]]:
    """
    Count the most common pairs of numbers in the historical draws.
    """
    counter = Counter()

    for draw in draws:
        counter.update(combinations(draw["numbers"], 2))

    return counter.most_common(limit)


def calculate_even_odd_distribution(draws: list[dict]) -> dict[str, int]:
    """
    Count historical even/odd patterns.
    """
    counter = Counter()

    for draw in draws:
        even_count = sum(1 for number in draw["numbers"] if number % 2 == 0)
        odd_count = DRAW_COUNT - even_count
        counter[f"{even_count} even / {odd_count} odd"] += 1

    return dict(counter)


def calculate_low_high_distribution(draws: list[dict]) -> dict[str, int]:
    """
    Count historical low/high patterns.

    Low numbers: 1-24
    High numbers: 25-49
    """
    counter = Counter()

    for draw in draws:
        low_count = sum(1 for number in draw["numbers"] if number <= 24)
        high_count = DRAW_COUNT - low_count
        counter[f"{low_count} low / {high_count} high"] += 1

    return dict(counter)


def calculate_sum_summary(draws: list[dict]) -> dict[str, float]:
    """
    Calculate min, max and average sum of historical combinations.
    """
    sums = [sum(draw["numbers"]) for draw in draws]

    if not sums:
        return {"min": 0, "max": 0, "average": 0.0}

    return {
        "min": min(sums),
        "max": max(sums),
        "average": sum(sums) / len(sums),
    }


def build_historical_report(draws: list[dict]) -> str:
    """
    Build a markdown report from historical draw analysis.
    """
    frequencies = calculate_number_frequencies(draws)
    gaps = calculate_recency_gaps(draws)
    hot_numbers = get_hot_numbers(frequencies)
    cold_numbers = get_cold_numbers(frequencies)
    overdue_numbers = get_overdue_numbers(gaps)
    pairs = calculate_pair_frequencies(draws)
    even_odd = calculate_even_odd_distribution(draws)
    low_high = calculate_low_high_distribution(draws)
    sum_summary = calculate_sum_summary(draws)

    lines = [
        "# Historical Lottery Analysis Report",
        "",
        "This report is based on historical 6/49 draw data.",
        "",
        "**Important:** This is not a prediction system. Lottery draws are random.",
        "The analysis is useful for training, statistics, and understanding probability.",
        "",
        f"Total historical draws analyzed: **{len(draws)}**",
        "",
        "## Most frequent numbers",
        "",
    ]

    for number, count in hot_numbers:
        lines.append(f"- {number}: {count} appearances")

    lines.extend(["", "## Least frequent numbers", ""])

    for number, count in cold_numbers:
        lines.append(f"- {number}: {count} appearances")

    lines.extend(["", "## Most overdue numbers", ""])

    for number, gap in overdue_numbers:
        lines.append(f"- {number}: not seen for {gap} draws")

    lines.extend(["", "## Most common pairs", ""])

    for pair, count in pairs:
        lines.append(f"- {pair[0]} + {pair[1]}: {count} times")

    lines.extend(["", "## Even/Odd distribution", ""])

    for pattern, count in sorted(even_odd.items()):
        lines.append(f"- {pattern}: {count} draws")

    lines.extend(["", "## Low/High distribution", ""])

    for pattern, count in sorted(low_high.items()):
        lines.append(f"- {pattern}: {count} draws")

    lines.extend(
        [
            "",
            "## Combination sum summary",
            "",
            f"- Minimum sum: {sum_summary['min']}",
            f"- Maximum sum: {sum_summary['max']}",
            f"- Average sum: {sum_summary['average']:.2f}",
            "",
        ]
    )

    return "\n".join(lines)


def write_historical_report(
    draws: list[dict],
    report_path: Path = DEFAULT_REPORT_PATH,
) -> Path:
    """
    Write the historical analysis report to a markdown file.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_historical_report(draws), encoding="utf-8")
    return report_path


def analyze_historical_draws(
    csv_path: Path = DEFAULT_DATA_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> dict:
    """
    Run the historical analysis and return a compact summary.
    """
    draws = load_historical_draws(csv_path)
    report_path = write_historical_report(draws, report_path)

    frequencies = calculate_number_frequencies(draws)
    gaps = calculate_recency_gaps(draws)

    return {
        "draw_count": len(draws),
        "report_path": str(report_path),
        "hot_numbers": get_hot_numbers(frequencies, limit=6),
        "cold_numbers": get_cold_numbers(frequencies, limit=6),
        "overdue_numbers": get_overdue_numbers(gaps, limit=6),
    }
