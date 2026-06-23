import csv
import json
import math
import random
from itertools import combinations
from pathlib import Path

from src.combination_filters import (
    calculate_historical_structure_profile,
    score_combination_structure,
)
from src.pair_model import (
    build_pair_counts,
    build_triple_counts,
    score_pair_support,
    score_triple_support,
)
from src.rolling_window_model import (
    build_rolling_window_scores,
    score_combination_rolling,
)
from src.simulation import count_matches


TOTAL_NUMBERS = 49
DRAW_COUNT = 6
TOTAL_COMBINATIONS = 13_983_816
THEORETICAL_JACKPOT_PROBABILITY = 1 / TOTAL_COMBINATIONS
BASELINE_NUMBER_PROBABILITY = DRAW_COUNT / TOTAL_NUMBERS

DEFAULT_DATA_PATH = Path("data") / "historical_draws.csv"
DEFAULT_COMBINED_MODEL_PATH = Path("models") / "lottery_combined_model.json"
DEFAULT_COMBINED_REPORT_PATH = Path("reports") / "combined_strategy_report.md"
DEFAULT_COMBINED_BACKTEST_REPORT_PATH = Path("reports") / "combined_backtest_report.md"

MODEL_PATHS = {
    "hot": Path("models") / "lottery_frequency_model.json",
    "cold": Path("models") / "lottery_cold_model.json",
    "middle": Path("models") / "lottery_middle_model.json",
    "gap": Path("models") / "lottery_gap_model.json",
}

COMBINED_WEIGHTS = {
    "hot": 0.12,
    "cold": 0.12,
    "middle": 0.13,
    "gap": 0.18,
    "pair": 0.12,
    "triple": 0.04,
    "structure": 0.16,
    "rolling": 0.13,
}


class CombinedModelError(Exception):
    """
    Raised when the combined strategy cannot be trained or evaluated.
    """


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def load_draws(csv_path: Path = DEFAULT_DATA_PATH) -> list[dict]:
    """
    Load historical lottery draws from CSV.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Historical data file not found: {csv_path}")

    draws = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required_columns = {"draw_id", "date", "n1", "n2", "n3", "n4", "n5", "n6"}
        fieldnames = set(reader.fieldnames or [])
        missing_columns = required_columns - fieldnames

        if missing_columns:
            raise ValueError(f"Missing columns in historical CSV: {missing_columns}")

        for row in reader:
            numbers = [int(row[f"n{index}"]) for index in range(1, 7)]
            if len(numbers) != DRAW_COUNT or len(set(numbers)) != DRAW_COUNT:
                raise ValueError(f"Invalid draw numbers in row: {row}")
            if any(number < 1 or number > TOTAL_NUMBERS for number in numbers):
                raise ValueError(f"Draw contains number outside 1-49: {row}")

            draws.append(
                {
                    "draw_id": int(row["draw_id"]),
                    "date": row["date"],
                    "numbers": sorted(numbers),
                }
            )

    if not draws:
        raise ValueError("Historical CSV has no draw rows.")

    return draws


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _normalize_score_map(raw_scores: dict[int, float]) -> dict[int, float]:
    """
    Normalize numeric scores to 0-1 while preserving rank.
    """
    values = list(raw_scores.values())
    if not values:
        return {number: 0.5 for number in range(1, TOTAL_NUMBERS + 1)}

    minimum = min(values)
    maximum = max(values)

    if math.isclose(minimum, maximum):
        return {number: 0.5 for number in range(1, TOTAL_NUMBERS + 1)}

    return {
        number: _clamp((raw_scores.get(number, minimum) - minimum) / (maximum - minimum))
        for number in range(1, TOTAL_NUMBERS + 1)
    }


def _model_scores_from_file(path: Path, score_field_candidates: list[str]) -> dict[int, float]:
    """
    Read number-level scores from an existing model JSON file.
    """
    model = _load_json(path)
    if not model:
        return {number: 0.5 for number in range(1, TOTAL_NUMBERS + 1)}

    scored_numbers = model.get("scored_numbers", [])
    raw_scores = {}

    for item in scored_numbers:
        number = int(item["number"])

        for field in score_field_candidates:
            if field in item:
                raw_scores[number] = _safe_float(item[field], default=0.0)
                break
        else:
            raw_scores[number] = 0.0

    return _normalize_score_map(raw_scores)


def build_number_model_scores() -> dict[str, dict[int, float]]:
    """
    Load normalized number scores from all previously trained models.
    """
    return {
        "hot": _model_scores_from_file(
            MODEL_PATHS["hot"],
            ["model_score", "score"],
        ),
        "cold": _model_scores_from_file(
            MODEL_PATHS["cold"],
            ["cold_model_score", "cold_score", "score"],
        ),
        "middle": _model_scores_from_file(
            MODEL_PATHS["middle"],
            ["middle_model_score", "middle_score", "score"],
        ),
        "gap": _model_scores_from_file(
            MODEL_PATHS["gap"],
            ["combined_next_probability", "gap_score", "score"],
        ),
    }


def generate_random_combination(rng: random.Random) -> list[int]:
    """
    Generate one random candidate combination.
    """
    return sorted(rng.sample(range(1, TOTAL_NUMBERS + 1), DRAW_COUNT))


def _top_numbers(score_map: dict[int, float], limit: int = DRAW_COUNT) -> list[int]:
    return [
        number
        for number, _score in sorted(
            score_map.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    ]


def generate_seed_combinations(number_model_scores: dict[str, dict[int, float]]) -> set[tuple[int, ...]]:
    """
    Generate deterministic candidates from existing model recommendations.
    """
    candidates = set()

    for model_name in ("hot", "cold", "middle", "gap"):
        candidates.add(tuple(sorted(_top_numbers(number_model_scores[model_name]))))

    hot = _top_numbers(number_model_scores["hot"], limit=12)
    cold = _top_numbers(number_model_scores["cold"], limit=12)
    middle = _top_numbers(number_model_scores["middle"], limit=12)
    gap = _top_numbers(number_model_scores["gap"], limit=12)

    strategies = [
        hot[:2] + cold[:2] + middle[:1] + gap[:1],
        hot[:1] + cold[:2] + middle[:1] + gap[:2],
        hot[:1] + cold[:1] + middle[:2] + gap[:2],
        hot[:2] + cold[:1] + middle[:2] + gap[:1],
        hot[:1] + cold[:1] + middle[:3] + gap[:1],
    ]

    for strategy in strategies:
        unique_numbers = sorted(set(strategy))
        filler_pool = hot + cold + middle + gap

        for number in filler_pool:
            if len(unique_numbers) == DRAW_COUNT:
                break
            if number not in unique_numbers:
                unique_numbers.append(number)
                unique_numbers.sort()

        if len(unique_numbers) == DRAW_COUNT:
            candidates.add(tuple(unique_numbers))

    return candidates


def generate_candidate_pool(
    number_model_scores: dict[str, dict[int, float]],
    candidate_count: int = 20_000,
    random_seed: int = 49,
) -> list[list[int]]:
    """
    Generate candidate combinations for the combined model to evaluate.
    """
    rng = random.Random(random_seed)
    candidates = generate_seed_combinations(number_model_scores)

    weighted_pool = []
    for model_name, score_map in number_model_scores.items():
        ranked_numbers = _top_numbers(score_map, limit=24)
        repeats = 4 if model_name in {"gap", "middle"} else 3
        for number in ranked_numbers:
            weighted_pool.extend([number] * repeats)

    weighted_pool.extend(range(1, TOTAL_NUMBERS + 1))

    while len(candidates) < candidate_count:
        if rng.random() < 0.60:
            candidate = sorted(set(rng.sample(weighted_pool, DRAW_COUNT * 2)))[:DRAW_COUNT]
            if len(candidate) < DRAW_COUNT:
                candidate = generate_random_combination(rng)
        else:
            candidate = generate_random_combination(rng)

        if len(candidate) == DRAW_COUNT and len(set(candidate)) == DRAW_COUNT:
            candidates.add(tuple(sorted(candidate)))

    return [list(candidate) for candidate in sorted(candidates)]


def _average_number_score(numbers: list[int], score_map: dict[int, float]) -> float:
    return sum(score_map.get(number, 0.5) for number in numbers) / len(numbers)


def score_candidate_combination(
    numbers: list[int],
    number_model_scores: dict[str, dict[int, float]],
    structure_profile: dict,
    pair_counts,
    triple_counts,
    rolling_scores: dict[int, dict],
) -> dict:
    """
    Score one candidate combination using all sub-models.
    """
    sorted_numbers = sorted(numbers)

    hot_score = _average_number_score(sorted_numbers, number_model_scores["hot"])
    cold_score = _average_number_score(sorted_numbers, number_model_scores["cold"])
    middle_score = _average_number_score(sorted_numbers, number_model_scores["middle"])
    gap_score = _average_number_score(sorted_numbers, number_model_scores["gap"])

    structure = score_combination_structure(sorted_numbers, structure_profile)
    pair_support = score_pair_support(sorted_numbers, pair_counts)
    triple_support = score_triple_support(sorted_numbers, triple_counts)
    rolling_support = score_combination_rolling(sorted_numbers, rolling_scores)

    final_score = (
        hot_score * COMBINED_WEIGHTS["hot"]
        + cold_score * COMBINED_WEIGHTS["cold"]
        + middle_score * COMBINED_WEIGHTS["middle"]
        + gap_score * COMBINED_WEIGHTS["gap"]
        + pair_support["pair_score"] * COMBINED_WEIGHTS["pair"]
        + triple_support["triple_score"] * COMBINED_WEIGHTS["triple"]
        + structure["structure_score"] * COMBINED_WEIGHTS["structure"]
        + rolling_support["rolling_score"] * COMBINED_WEIGHTS["rolling"]
    )

    return {
        "numbers": sorted_numbers,
        "final_score": _clamp(final_score),
        "confidence_score": _clamp(final_score) * 100,
        "sub_scores": {
            "hot_score": hot_score,
            "cold_score": cold_score,
            "middle_score": middle_score,
            "gap_probability_score": gap_score,
            "pair_score": pair_support["pair_score"],
            "triple_score": triple_support["triple_score"],
            "structure_score": structure["structure_score"],
            "rolling_window_score": rolling_support["rolling_score"],
        },
        "structure_details": structure,
        "pair_details": pair_support,
        "triple_details": triple_support,
        "rolling_details": rolling_support,
        "theoretical_jackpot_probability": THEORETICAL_JACKPOT_PROBABILITY,
        "theoretical_jackpot_odds": f"1 in {TOTAL_COMBINATIONS}",
    }


def add_relative_probabilities(scored_candidates: list[dict], temperature: float = 0.08) -> list[dict]:
    """
    Add relative model probability and percentile rank inside the generated pool.

    This is not the true lottery probability. It is a relative probability mass
    among the candidates generated by this model.
    """
    if not scored_candidates:
        return scored_candidates

    max_score = max(candidate["final_score"] for candidate in scored_candidates)
    weights = [
        math.exp((candidate["final_score"] - max_score) / temperature)
        for candidate in scored_candidates
    ]
    total_weight = sum(weights)

    total_candidates = len(scored_candidates)

    for index, (candidate, weight) in enumerate(zip(scored_candidates, weights), start=1):
        candidate["relative_model_probability"] = weight / total_weight if total_weight else 0.0
        candidate["relative_rank"] = index
        candidate["relative_top_percent"] = (index / total_candidates) * 100

    return scored_candidates


def train_combined_strategy_model(
    csv_path: Path = DEFAULT_DATA_PATH,
    candidate_count: int = 20_000,
    top_limit: int = 20,
    random_seed: int = 49,
) -> dict:
    """
    Train the final combined strategy model.
    """
    draws = load_draws(csv_path)
    number_model_scores = build_number_model_scores()
    structure_profile = calculate_historical_structure_profile(draws)
    pair_counts = build_pair_counts(draws)
    triple_counts = build_triple_counts(draws)
    rolling_scores = build_rolling_window_scores(draws)

    candidates = generate_candidate_pool(
        number_model_scores,
        candidate_count=candidate_count,
        random_seed=random_seed,
    )

    scored_candidates = [
        score_candidate_combination(
            candidate,
            number_model_scores,
            structure_profile,
            pair_counts,
            triple_counts,
            rolling_scores,
        )
        for candidate in candidates
    ]

    scored_candidates.sort(
        key=lambda item: (-item["final_score"], item["numbers"]),
    )
    scored_candidates = add_relative_probabilities(scored_candidates)

    model = {
        "model_name": "Final Combined Prediction Strategy Model",
        "model_version": "1.0",
        "training_draws": len(draws),
        "candidate_count": len(scored_candidates),
        "weights": COMBINED_WEIGHTS,
        "theoretical_jackpot_probability": THEORETICAL_JACKPOT_PROBABILITY,
        "theoretical_jackpot_odds": f"1 in {TOTAL_COMBINATIONS}",
        "important_note": (
            "This model does not change the real lottery jackpot probability. "
            "It gives a relative statistical confidence score among generated candidates."
        ),
        "recommended_combinations": scored_candidates[:top_limit],
    }

    return model


def save_combined_model(
    model: dict,
    model_path: Path = DEFAULT_COMBINED_MODEL_PATH,
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)

    with model_path.open("w", encoding="utf-8") as file:
        json.dump(model, file, indent=2)


def load_combined_model(model_path: Path = DEFAULT_COMBINED_MODEL_PATH) -> dict:
    if not model_path.exists():
        raise FileNotFoundError(f"Combined model not found: {model_path}")

    with model_path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_combined_report(
    model: dict,
    report_path: Path = DEFAULT_COMBINED_REPORT_PATH,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Final Combined Prediction Strategy Model",
        "",
        "This report summarizes the final ensemble-style model.",
        "",
        "Important: this model does not change the real mathematical jackpot probability.",
        "It ranks generated combinations by statistical profile and model confidence.",
        "",
        f"Training draws: {model['training_draws']}",
        f"Generated candidate combinations: {model['candidate_count']}",
        f"Theoretical jackpot odds per combination: {model['theoretical_jackpot_odds']}",
        "",
        "## Weights",
        "",
    ]

    for name, value in model["weights"].items():
        lines.append(f"- {name}: {value:.2f}")

    lines.extend(["", "## Recommended combinations", ""])

    for item in model["recommended_combinations"]:
        sub_scores = item["sub_scores"]
        structure = item["structure_details"]
        lines.extend(
            [
                f"### Rank {item['relative_rank']}: {item['numbers']}",
                "",
                f"- Confidence score: {item['confidence_score']:.2f}/100",
                f"- Relative model probability inside candidate pool: {item['relative_model_probability']:.6%}",
                f"- Relative rank: top {item['relative_top_percent']:.2f}%",
                f"- Theoretical jackpot odds: {item['theoretical_jackpot_odds']}",
                f"- Hot score: {sub_scores['hot_score']:.4f}",
                f"- Cold score: {sub_scores['cold_score']:.4f}",
                f"- Middle score: {sub_scores['middle_score']:.4f}",
                f"- Gap probability score: {sub_scores['gap_probability_score']:.4f}",
                f"- Pair score: {sub_scores['pair_score']:.4f}",
                f"- Triple score: {sub_scores['triple_score']:.4f}",
                f"- Structure score: {sub_scores['structure_score']:.4f}",
                f"- Rolling window score: {sub_scores['rolling_window_score']:.4f}",
                f"- Sum: {structure['sum']}",
                f"- Even/Odd: {structure['even_count']}/{structure['odd_count']}",
                f"- Low/High: {structure['low_count']}/{structure['high_count']}",
                f"- Consecutive pairs: {structure['consecutive_pairs']}",
                "",
            ]
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_combined_backtest(
    csv_path: Path = DEFAULT_DATA_PATH,
    max_test_draws: int = 25,
    candidate_count: int = 5_000,
    random_seed: int = 2026,
) -> dict:
    """
    Run a lightweight rolling backtest for the combined model.

    The backtest retrains on the past and tests against the next real draw.
    It is intentionally conservative and uses fewer generated candidates per step.
    """
    draws = load_draws(csv_path)

    if len(draws) < 12:
        return {
            "tested_draws": 0,
            "combined_average_matches": 0.0,
            "random_average_matches": 0.0,
            "message": "Not enough draws for a meaningful combined backtest.",
            "details": [],
        }

    rng = random.Random(random_seed)
    start_index = max(8, len(draws) - max_test_draws)
    details = []

    for test_index in range(start_index, len(draws)):
        training_draws = draws[:test_index]
        actual_draw = draws[test_index]

        # Build a temporary model from in-memory training draws.
        # The helper uses model JSONs for number-level scores, so this backtest
        # is a practical strategy check, not a full nested retraining of every sub-model.
        number_model_scores = build_number_model_scores()
        structure_profile = calculate_historical_structure_profile(training_draws)
        pair_counts = build_pair_counts(training_draws)
        triple_counts = build_triple_counts(training_draws)
        rolling_scores = build_rolling_window_scores(training_draws)
        candidates = generate_candidate_pool(
            number_model_scores,
            candidate_count=candidate_count,
            random_seed=random_seed + test_index,
        )

        scored_candidates = [
            score_candidate_combination(
                candidate,
                number_model_scores,
                structure_profile,
                pair_counts,
                triple_counts,
                rolling_scores,
            )
            for candidate in candidates
        ]
        scored_candidates.sort(key=lambda item: (-item["final_score"], item["numbers"]))

        combined_ticket = scored_candidates[0]["numbers"]
        random_ticket = sorted(rng.sample(range(1, TOTAL_NUMBERS + 1), DRAW_COUNT))

        details.append(
            {
                "draw_id": actual_draw["draw_id"],
                "date": actual_draw["date"],
                "actual_numbers": actual_draw["numbers"],
                "combined_ticket": combined_ticket,
                "combined_matches": count_matches(combined_ticket, actual_draw["numbers"]),
                "random_ticket": random_ticket,
                "random_matches": count_matches(random_ticket, actual_draw["numbers"]),
            }
        )

    tested_draws = len(details)
    combined_average = sum(item["combined_matches"] for item in details) / tested_draws
    random_average = sum(item["random_matches"] for item in details) / tested_draws

    if combined_average > random_average:
        message = "Combined model performed better than random in this run."
    elif combined_average < random_average:
        message = "Random baseline performed better than combined model in this run."
    else:
        message = "Combined model and random baseline tied in this run."

    return {
        "tested_draws": tested_draws,
        "combined_average_matches": combined_average,
        "random_average_matches": random_average,
        "message": message + " Use real historical data before drawing conclusions.",
        "details": details,
    }


def write_combined_backtest_report(
    backtest: dict,
    report_path: Path = DEFAULT_COMBINED_BACKTEST_REPORT_PATH,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Combined Strategy Backtest Report",
        "",
        f"Проверени тиражи: {backtest['tested_draws']}",
        f"Combined model average matches: {backtest['combined_average_matches']:.4f}",
        f"Random baseline average matches: {backtest['random_average_matches']:.4f}",
        "",
        backtest["message"],
        "",
        "## Details",
        "",
    ]

    for item in backtest.get("details", []):
        lines.append(
            f"- Draw {item['draw_id']} ({item['date']}): "
            f"actual={item['actual_numbers']}, "
            f"combined={item['combined_ticket']} ({item['combined_matches']} matches), "
            f"random={item['random_ticket']} ({item['random_matches']} matches)"
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")
