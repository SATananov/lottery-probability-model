import csv
import json
import math
from pathlib import Path


TOTAL_NUMBERS = 49
DRAW_COUNT = 6
NUMBER_COLUMNS = ["n1", "n2", "n3", "n4", "n5", "n6"]

DEFAULT_DATA_PATH = Path("data") / "historical_draws.csv"
DEFAULT_MODEL_PATH = Path("models") / "lottery_frequency_model.json"
DEFAULT_REPORT_PATH = Path("reports") / "frequency_model_report.md"


def _clean_header(header: str) -> str:
    """
    Remove invisible characters that sometimes appear in CSV headers.
    """
    return header.replace("\ufeff", "").strip()


def load_draws(csv_path: Path = DEFAULT_DATA_PATH) -> list[dict]:
    """
    Load historical 6/49 draws from CSV.

    Expected columns:
    draw_id,date,n1,n2,n3,n4,n5,n6
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Historical data file not found: {csv_path}")

    draws = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError("Historical data file is empty.")

        reader.fieldnames = [_clean_header(field) for field in reader.fieldnames]
        required_columns = {"draw_id", "date", *NUMBER_COLUMNS}
        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(f"Missing columns in historical CSV: {missing_columns}")

        for row_index, row in enumerate(reader, start=2):
            cleaned_row = {_clean_header(key): value for key, value in row.items()}

            try:
                numbers = [int(cleaned_row[column]) for column in NUMBER_COLUMNS]
            except ValueError as error:
                raise ValueError(
                    f"Invalid number value on CSV row {row_index}: {cleaned_row}"
                ) from error

            validate_draw_numbers(numbers, row_index)

            draws.append(
                {
                    "draw_id": str(cleaned_row["draw_id"]),
                    "date": str(cleaned_row["date"]),
                    "numbers": sorted(numbers),
                }
            )

    return draws


def validate_draw_numbers(numbers: list[int], row_index: int | None = None) -> None:
    """
    Validate one 6/49 draw.
    """
    location = f" on CSV row {row_index}" if row_index is not None else ""

    if len(numbers) != DRAW_COUNT:
        raise ValueError(f"Each draw must contain exactly 6 numbers{location}.")

    if len(set(numbers)) != DRAW_COUNT:
        raise ValueError(f"Draw contains duplicate numbers{location}: {numbers}")

    invalid_numbers = [
        number for number in numbers
        if number < 1 or number > TOTAL_NUMBERS
    ]

    if invalid_numbers:
        raise ValueError(f"Draw contains invalid numbers{location}: {invalid_numbers}")


def count_number_occurrences(draws: list[dict]) -> dict[int, int]:
    """
    Count how many draws contain each number from 1 to 49.
    """
    counts = {number: 0 for number in range(1, TOTAL_NUMBERS + 1)}

    for draw in draws:
        for number in draw["numbers"]:
            counts[number] += 1

    return counts


def calculate_recent_counts(draws: list[dict], window: int = 20) -> dict[int, int]:
    """
    Count how many times each number appears in the last N draws.
    """
    recent_draws = draws[-window:] if window > 0 else draws
    return count_number_occurrences(recent_draws)


def calculate_recency_gaps(draws: list[dict]) -> dict[int, int]:
    """
    Calculate how many draws have passed since each number last appeared.

    Gap = 0 means the number appeared in the latest draw.
    Higher gap means the number has not appeared for longer.
    """
    gaps = {}

    for number in range(1, TOTAL_NUMBERS + 1):
        gap = len(draws)

        for reverse_index, draw in enumerate(reversed(draws)):
            if number in draw["numbers"]:
                gap = reverse_index
                break

        gaps[number] = gap

    return gaps


def build_number_statistics(draws: list[dict], recent_window: int = 20) -> list[dict]:
    """
    Build detailed statistics for every number from 1 to 49.

    This is the training step for the historical frequency model.
    """
    if not draws:
        raise ValueError("Cannot train frequency model without historical draws.")

    total_draws = len(draws)
    theoretical_probability = DRAW_COUNT / TOTAL_NUMBERS
    expected_count = total_draws * theoretical_probability

    counts = count_number_occurrences(draws)
    recent_counts = calculate_recent_counts(draws, window=recent_window)
    gaps = calculate_recency_gaps(draws)

    actual_recent_window = min(recent_window, total_draws)
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
        z_score = (
            (count - expected_count) / standard_deviation
            if standard_deviation > 0
            else 0
        )

        if z_score >= 2:
            status = "HOT"
        elif z_score <= -2:
            status = "COLD"
        else:
            status = "NORMAL"

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
                "z_score": z_score,
                "status": status,
            }
        )

    return statistics


def train_frequency_model(
    draws: list[dict],
    recent_window: int = 20,
    frequency_weight: float = 0.55,
    recent_weight: float = 0.30,
    gap_weight: float = 0.15,
) -> dict:
    """
    Train a transparent historical frequency scoring model.

    The model is intentionally simple:
    - historical frequency score
    - recent frequency score
    - recency gap score

    It does not guarantee future lottery results. It only ranks numbers
    based on patterns observed in historical data.
    """
    if not math.isclose(
        frequency_weight + recent_weight + gap_weight,
        1.0,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        raise ValueError("Model weights must sum to 1.0.")

    statistics = build_number_statistics(draws, recent_window=recent_window)
    theoretical_probability = DRAW_COUNT / TOTAL_NUMBERS

    max_gap = max(item["recency_gap"] for item in statistics) or 1
    scored_numbers = []

    for item in statistics:
        frequency_ratio = (
            item["empirical_probability"] / theoretical_probability
            if theoretical_probability > 0
            else 0
        )
        recent_ratio = (
            item["recent_probability"] / theoretical_probability
            if theoretical_probability > 0
            else 0
        )
        gap_score = item["recency_gap"] / max_gap

        score = (
            frequency_weight * frequency_ratio
            + recent_weight * recent_ratio
            + gap_weight * gap_score
        )

        scored_item = {
            **item,
            "frequency_ratio": frequency_ratio,
            "recent_ratio": recent_ratio,
            "gap_score": gap_score,
            "model_score": score,
        }

        scored_numbers.append(scored_item)

    scored_numbers = sorted(
        scored_numbers,
        key=lambda item: (-item["model_score"], item["number"]),
    )

    recommended_ticket = sorted(item["number"] for item in scored_numbers[:DRAW_COUNT])

    return {
        "model_name": "Historical Frequency Probability Model",
        "model_version": "1.0",
        "total_numbers": TOTAL_NUMBERS,
        "draw_count": DRAW_COUNT,
        "training_draws": len(draws),
        "recent_window": min(recent_window, len(draws)),
        "weights": {
            "historical_frequency": frequency_weight,
            "recent_frequency": recent_weight,
            "recency_gap": gap_weight,
        },
        "method_note": (
            "This is a transparent statistical training model. "
            "It ranks numbers using historical frequency, recent frequency, "
            "and recency gaps. It does not prove or guarantee future outcomes."
        ),
        "recommended_ticket": recommended_ticket,
        "scored_numbers": scored_numbers,
    }


def save_model(model: dict, model_path: Path = DEFAULT_MODEL_PATH) -> Path:
    """
    Save the trained model as JSON.
    """
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    with model_path.open("w", encoding="utf-8") as model_file:
        json.dump(model, model_file, indent=2)

    return model_path


def load_model(model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    """
    Load a trained model from JSON.
    """
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. Run python train_model.py first."
        )

    with model_path.open("r", encoding="utf-8") as model_file:
        return json.load(model_file)


def get_top_numbers(model: dict, limit: int = 10) -> list[dict]:
    """
    Return the top scored numbers from a trained model.
    """
    return model["scored_numbers"][:limit]


def write_frequency_model_report(
    model: dict,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> Path:
    """
    Write a readable markdown report for the trained frequency model.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    top_numbers = get_top_numbers(model, limit=10)
    bottom_numbers = sorted(
        model["scored_numbers"],
        key=lambda item: (item["model_score"], item["number"]),
    )[:10]

    lines = [
        "# Frequency Model Report",
        "",
        "## Model",
        "",
        f"- Name: {model['model_name']}",
        f"- Version: {model['model_version']}",
        f"- Training draws: {model['training_draws']}",
        f"- Последен прозорец: {model['recent_window']}",
        f"- Recommended ticket: {model['recommended_ticket']}",
        "",
        "## Important warning",
        "",
        (
            "This model does not predict lottery results with certainty. "
            "It only ranks numbers using historical frequencies and simple "
            "statistical scoring."
        ),
        "",
        "## Weights",
        "",
        f"- Historical frequency: {model['weights']['historical_frequency']}",
        f"- Recent frequency: {model['weights']['recent_frequency']}",
        f"- Recency gap: {model['weights']['recency_gap']}",
        "",
        "## Top scored numbers",
        "",
        "| Number | Score | Times drawn | Empirical probability | Expected probability | Z-score | Status | Gap |",
        "|---:|---:|---:|---:|---:|---:|:---|---:|",
    ]

    for item in top_numbers:
        lines.append(
            "| {number} | {score:.4f} | {times} | {emp:.4%} | {theoretical:.4%} | {z:.2f} | {status} | {gap} |".format(
                number=item["number"],
                score=item["model_score"],
                times=item["times_drawn"],
                emp=item["empirical_probability"],
                theoretical=item["theoretical_probability"],
                z=item["z_score"],
                status=item["status"],
                gap=item["recency_gap"],
            )
        )

    lines.extend(
        [
            "",
            "## Lowest scored numbers",
            "",
            "| Number | Score | Times drawn | Empirical probability | Expected probability | Z-score | Status | Gap |",
            "|---:|---:|---:|---:|---:|---:|:---|---:|",
        ]
    )

    for item in bottom_numbers:
        lines.append(
            "| {number} | {score:.4f} | {times} | {emp:.4%} | {theoretical:.4%} | {z:.2f} | {status} | {gap} |".format(
                number=item["number"],
                score=item["model_score"],
                times=item["times_drawn"],
                emp=item["empirical_probability"],
                theoretical=item["theoretical_probability"],
                z=item["z_score"],
                status=item["status"],
                gap=item["recency_gap"],
            )
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path