from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

TOTAL_NUMBERS = 49
DRAW_SIZE = 6
TOTAL_COMBINATIONS = math.comb(TOTAL_NUMBERS, DRAW_SIZE)
BASELINE_NUMBER_PROBABILITY = DRAW_SIZE / TOTAL_NUMBERS
DEFAULT_DATA_PATH = Path("data") / "historical_draws.csv"
DEFAULT_MODEL_PATH = Path("models") / "lottery_advanced_ensemble_model.json"
DEFAULT_REPORT_PATH = Path("reports") / "advanced_ensemble_report.md"
DEFAULT_BACKTEST_REPORT_PATH = Path("reports") / "advanced_backtest_report.md"
DEFAULT_BACKTEST_JSON_PATH = Path("models") / "lottery_advanced_backtest.json"

ADVANCED_WEIGHTS = {
    "time_decay": 0.18,
    "bayesian": 0.16,
    "gap": 0.16,
    "pair_significance": 0.12,
    "triple_significance": 0.05,
    "structure_balance": 0.14,
    "human_pattern_avoidance": 0.14,
    "frequency_stability": 0.05,
}


class AdvancedModelError(Exception):
    """Raised when the advanced analysis cannot be completed."""


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_draws(csv_path: Path = DEFAULT_DATA_PATH) -> list[dict[str, Any]]:
    """Read and validate historical draw rows."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Historical draw file not found: {csv_path}")

    draws: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"draw_id", "date", "year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {sorted(missing)}")

        for row in reader:
            numbers = sorted(int(row[f"n{idx}"]) for idx in range(1, 7))
            if len(numbers) != DRAW_SIZE or len(set(numbers)) != DRAW_SIZE:
                raise ValueError(f"Invalid draw numbers: {row}")
            if any(number < 1 or number > TOTAL_NUMBERS for number in numbers):
                raise ValueError(f"Number outside 1-49: {row}")
            draws.append(
                {
                    "draw_id": int(row["draw_id"]),
                    "date": row["date"],
                    "year": int(row["year"]),
                    "draw_number": int(row["draw_number"]),
                    "draw_position": int(row["draw_position"]),
                    "numbers": numbers,
                }
            )

    if not draws:
        raise ValueError("Historical draw file is empty.")
    return draws


def _normalize_map(raw_scores: dict[int, float], default: float = 0.5) -> dict[int, float]:
    values = [raw_scores.get(number, default) for number in range(1, TOTAL_NUMBERS + 1)]
    minimum = min(values)
    maximum = max(values)
    if math.isclose(minimum, maximum):
        return {number: default for number in range(1, TOTAL_NUMBERS + 1)}
    return {
        number: _clamp((raw_scores.get(number, minimum) - minimum) / (maximum - minimum))
        for number in range(1, TOTAL_NUMBERS + 1)
    }


def _regularized_gamma_q(a: float, x: float) -> float:
    """Upper regularized incomplete gamma Q(a, x), used for chi-square p-value."""
    if x < 0 or a <= 0:
        return float("nan")
    if x == 0:
        return 1.0

    eps = 3.0e-12
    fpmin = 1.0e-300
    max_iter = 200

    def gamma_p_series() -> float:
        ap = a
        summation = 1.0 / a
        delta = summation
        for _ in range(max_iter):
            ap += 1.0
            delta *= x / ap
            summation += delta
            if abs(delta) < abs(summation) * eps:
                break
        return summation * math.exp(-x + a * math.log(x) - math.lgamma(a))

    def gamma_q_continued_fraction() -> float:
        b = x + 1.0 - a
        c = 1.0 / fpmin
        d = 1.0 / max(b, fpmin)
        h = d
        for i in range(1, max_iter + 1):
            an = -i * (i - a)
            b += 2.0
            d = an * d + b
            if abs(d) < fpmin:
                d = fpmin
            c = b + an / c
            if abs(c) < fpmin:
                c = fpmin
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < eps:
                break
        return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h

    if x < a + 1.0:
        return _clamp(1.0 - gamma_p_series())
    return _clamp(gamma_q_continued_fraction())


def chi_square_fairness_test(draws: list[dict[str, Any]]) -> dict[str, Any]:
    """Check whether number frequencies are close to a fair 6/49 distribution."""
    draw_count = len(draws)
    expected_count = draw_count * BASELINE_NUMBER_PROBABILITY
    counts = Counter(number for draw in draws for number in draw["numbers"])
    chi_square = sum(((counts[number] - expected_count) ** 2) / expected_count for number in range(1, TOTAL_NUMBERS + 1))
    degrees_of_freedom = TOTAL_NUMBERS - 1
    p_value = _regularized_gamma_q(degrees_of_freedom / 2.0, chi_square / 2.0)
    z_scores = {
        number: (counts[number] - expected_count) / math.sqrt(expected_count * (1.0 - BASELINE_NUMBER_PROBABILITY))
        for number in range(1, TOTAL_NUMBERS + 1)
    }
    max_abs_z_number, max_abs_z = max(((number, abs(score)) for number, score in z_scores.items()), key=lambda item: item[1])

    if p_value < 0.01:
        interpretation = "Strong frequency deviation warning. Inspect the data source and parsing carefully."
    elif p_value < 0.05:
        interpretation = "Moderate frequency deviation warning. The result may still be random noise."
    else:
        interpretation = "No strong evidence against fair-looking number frequencies."

    return {
        "draw_count": draw_count,
        "expected_count_per_number": expected_count,
        "chi_square": chi_square,
        "degrees_of_freedom": degrees_of_freedom,
        "p_value": p_value,
        "max_abs_z_number": max_abs_z_number,
        "max_abs_z": max_abs_z,
        "interpretation": interpretation,
        "number_z_scores": z_scores,
    }


def build_number_statistics(
    draws: list[dict[str, Any]],
    half_life_draws: int = 500,
    bayesian_prior_strength: float = 49.0,
) -> dict[int, dict[str, Any]]:
    """Build frequency, time-decay, Bayesian and gap statistics for every number."""
    draw_count = len(draws)
    counts = Counter(number for draw in draws for number in draw["numbers"])
    appearances: dict[int, list[int]] = {number: [] for number in range(1, TOTAL_NUMBERS + 1)}
    weighted_counts = {number: 0.0 for number in range(1, TOTAL_NUMBERS + 1)}
    total_weight = 0.0

    for index, draw in enumerate(draws):
        age = len(draws) - 1 - index
        weight = 0.5 ** (age / max(1, half_life_draws))
        total_weight += weight
        for number in draw["numbers"]:
            appearances[number].append(index)
            weighted_counts[number] += weight

    expected_count = draw_count * BASELINE_NUMBER_PROBABILITY
    variance = expected_count * (1.0 - BASELINE_NUMBER_PROBABILITY)
    std = math.sqrt(max(variance, 1.0e-12))

    alpha_prior = bayesian_prior_strength * BASELINE_NUMBER_PROBABILITY
    beta_prior = bayesian_prior_strength * (1.0 - BASELINE_NUMBER_PROBABILITY)

    raw_time_decay = {}
    raw_bayesian = {}
    raw_gap = {}
    raw_frequency_stability = {}

    stats: dict[int, dict[str, Any]] = {}
    for number in range(1, TOTAL_NUMBERS + 1):
        count = counts[number]
        empirical_probability = count / draw_count
        z_score = (count - expected_count) / std
        posterior_probability = (alpha_prior + count) / (alpha_prior + beta_prior + draw_count)
        time_decay_probability = weighted_counts[number] / total_weight if total_weight else BASELINE_NUMBER_PROBABILITY

        positions = appearances[number]
        if positions:
            current_gap = len(draws) - 1 - positions[-1]
            intervals = [later - earlier for earlier, later in zip(positions, positions[1:])]
            average_interval = sum(intervals) / len(intervals) if intervals else 1.0 / BASELINE_NUMBER_PROBABILITY
        else:
            current_gap = len(draws)
            average_interval = 1.0 / BASELINE_NUMBER_PROBABILITY

        gap_ratio = current_gap / max(average_interval, 1.0)

        raw_time_decay[number] = time_decay_probability
        raw_bayesian[number] = posterior_probability
        raw_gap[number] = gap_ratio
        raw_frequency_stability[number] = 1.0 / (1.0 + abs(z_score))

        stats[number] = {
            "number": number,
            "count": count,
            "empirical_probability": empirical_probability,
            "expected_probability": BASELINE_NUMBER_PROBABILITY,
            "z_score": z_score,
            "time_decay_probability": time_decay_probability,
            "bayesian_posterior_probability": posterior_probability,
            "current_gap": current_gap,
            "average_interval": average_interval,
            "gap_ratio": gap_ratio,
        }

    time_decay_scores = _normalize_map(raw_time_decay)
    bayesian_scores = _normalize_map(raw_bayesian)
    gap_scores = _normalize_map(raw_gap)
    stability_scores = _normalize_map(raw_frequency_stability)

    for number in range(1, TOTAL_NUMBERS + 1):
        stats[number].update(
            {
                "time_decay_score": time_decay_scores[number],
                "bayesian_score": bayesian_scores[number],
                "gap_score": gap_scores[number],
                "frequency_stability_score": stability_scores[number],
            }
        )
        stats[number]["advanced_number_score"] = (
            stats[number]["time_decay_score"] * 0.30
            + stats[number]["bayesian_score"] * 0.25
            + stats[number]["gap_score"] * 0.25
            + stats[number]["frequency_stability_score"] * 0.20
        )

    return stats


def _event_probability_for_k_numbers(k: int) -> float:
    if k < 1 or k > DRAW_SIZE:
        return 0.0
    return math.comb(DRAW_SIZE, k) / math.comb(TOTAL_NUMBERS, k)


def build_pair_significance(draws: list[dict[str, Any]], top_limit: int = 50) -> dict[str, Any]:
    draw_count = len(draws)
    pair_counts = Counter()
    for draw in draws:
        for pair in combinations(draw["numbers"], 2):
            pair_counts[tuple(pair)] += 1

    p_pair = _event_probability_for_k_numbers(2)
    expected = draw_count * p_pair
    std = math.sqrt(max(draw_count * p_pair * (1.0 - p_pair), 1.0e-12))
    scored_pairs = []
    z_map = {}

    for pair, count in pair_counts.items():
        z_score = (count - expected) / std
        z_map[pair] = z_score
        scored_pairs.append(
            {
                "pair": list(pair),
                "count": count,
                "expected": expected,
                "z_score": z_score,
                "support_score": _clamp(0.5 + z_score / 8.0),
            }
        )

    scored_pairs.sort(key=lambda item: (-item["z_score"], item["pair"]))
    return {
        "draw_count": draw_count,
        "expected_pair_count": expected,
        "top_pairs": scored_pairs[:top_limit],
        "pair_z_scores": {"-".join(map(str, pair)): score for pair, score in z_map.items()},
    }


def build_triple_significance(draws: list[dict[str, Any]], top_limit: int = 30) -> dict[str, Any]:
    draw_count = len(draws)
    triple_counts = Counter()
    for draw in draws:
        for triple in combinations(draw["numbers"], 3):
            triple_counts[tuple(triple)] += 1

    p_triple = _event_probability_for_k_numbers(3)
    expected = draw_count * p_triple
    std = math.sqrt(max(draw_count * p_triple * (1.0 - p_triple), 1.0e-12))
    scored_triples = []
    z_map = {}

    for triple, count in triple_counts.items():
        z_score = (count - expected) / std
        z_map[triple] = z_score
        scored_triples.append(
            {
                "triple": list(triple),
                "count": count,
                "expected": expected,
                "z_score": z_score,
                "support_score": _clamp(0.5 + z_score / 8.0),
            }
        )

    scored_triples.sort(key=lambda item: (-item["z_score"], item["triple"]))
    return {
        "draw_count": draw_count,
        "expected_triple_count": expected,
        "top_triples": scored_triples[:top_limit],
        "triple_z_scores": {"-".join(map(str, triple)): score for triple, score in z_map.items()},
    }


def human_pattern_score(numbers: list[int]) -> dict[str, Any]:
    """Score how much a ticket avoids common human-picked patterns."""
    nums = sorted(numbers)
    penalties: list[str] = []
    score = 1.0

    under_32 = sum(1 for number in nums if number <= 31)
    if under_32 == 6:
        score -= 0.18
        penalties.append("all_numbers_are_birthdate_range_1_31")
    elif under_32 >= 5:
        score -= 0.08
        penalties.append("mostly_birthdate_range_1_31")

    consecutive_pairs = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
    if consecutive_pairs >= 3:
        score -= 0.18
        penalties.append("many_consecutive_pairs")
    elif consecutive_pairs >= 2:
        score -= 0.10
        penalties.append("some_consecutive_pairs")

    differences = [b - a for a, b in zip(nums, nums[1:])]
    if len(set(differences)) == 1:
        score -= 0.20
        penalties.append("perfect_arithmetic_sequence")

    ending_counts = Counter(number % 10 for number in nums)
    if ending_counts and max(ending_counts.values()) >= 4:
        score -= 0.12
        penalties.append("too_many_same_last_digits")

    decade_counts = Counter(number // 10 for number in nums)
    if decade_counts and max(decade_counts.values()) >= 4:
        score -= 0.10
        penalties.append("too_many_numbers_in_same_decade")

    odd_count = sum(1 for number in nums if number % 2)
    if odd_count in {0, 6}:
        score -= 0.14
        penalties.append("all_even_or_all_odd")
    elif odd_count in {1, 5}:
        score -= 0.06
        penalties.append("unbalanced_even_odd")

    total_sum = sum(nums)
    if total_sum < 85 or total_sum > 220:
        score -= 0.18
        penalties.append("extreme_sum")
    elif total_sum < 105 or total_sum > 195:
        score -= 0.08
        penalties.append("borderline_sum")

    spread = nums[-1] - nums[0]
    if spread < 20:
        score -= 0.10
        penalties.append("narrow_number_spread")

    return {
        "human_pattern_avoidance_score": _clamp(score),
        "penalties": penalties,
        "sum": total_sum,
        "odd_count": odd_count,
        "even_count": DRAW_SIZE - odd_count,
        "consecutive_pairs": consecutive_pairs,
        "spread": spread,
        "birthdate_range_count": under_32,
    }


def structure_balance_score(numbers: list[int]) -> dict[str, Any]:
    nums = sorted(numbers)
    total_sum = sum(nums)
    odd_count = sum(1 for number in nums if number % 2)
    low_count = sum(1 for number in nums if number <= 24)
    consecutive_pairs = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)

    sum_score = _clamp(1.0 - abs(total_sum - 150.0) / 95.0)
    odd_even_score = _clamp(1.0 - abs(odd_count - 3.0) / 3.0)
    low_high_score = _clamp(1.0 - abs(low_count - 3.0) / 3.0)
    consecutive_score = _clamp(1.0 - consecutive_pairs / 4.0)
    score = 0.35 * sum_score + 0.25 * odd_even_score + 0.25 * low_high_score + 0.15 * consecutive_score

    return {
        "structure_balance_score": _clamp(score),
        "sum_score": sum_score,
        "odd_even_score": odd_even_score,
        "low_high_score": low_high_score,
        "consecutive_score": consecutive_score,
    }


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pair_support(numbers: list[int], pair_z_scores: dict[str, float]) -> float:
    values = []
    for pair in combinations(sorted(numbers), 2):
        z = pair_z_scores.get("-".join(map(str, pair)), 0.0)
        values.append(_clamp(0.5 + z / 8.0))
    return _average(values) if values else 0.5


def _triple_support(numbers: list[int], triple_z_scores: dict[str, float]) -> float:
    values = []
    for triple in combinations(sorted(numbers), 3):
        z = triple_z_scores.get("-".join(map(str, triple)), 0.0)
        values.append(_clamp(0.5 + z / 8.0))
    return _average(values) if values else 0.5


def generate_advanced_candidates(number_stats: dict[int, dict[str, Any]], candidate_limit: int = 18_000, random_seed: int = 2026) -> list[list[int]]:
    """Generate a mix of deterministic and randomized candidates."""
    rng = random.Random(random_seed)
    candidates: set[tuple[int, ...]] = set()

    score_names = [
        "advanced_number_score",
        "time_decay_score",
        "bayesian_score",
        "gap_score",
        "frequency_stability_score",
    ]
    ranked_lists = {}
    for score_name in score_names:
        ranked_lists[score_name] = [
            item[0]
            for item in sorted(number_stats.items(), key=lambda item: (-item[1][score_name], item[0]))[:18]
        ]
        candidates.add(tuple(sorted(ranked_lists[score_name][:DRAW_SIZE])))

    balanced_pool = sorted(
        number_stats,
        key=lambda number: (
            -number_stats[number]["advanced_number_score"],
            abs(number_stats[number]["z_score"]),
            number,
        ),
    )[:20]

    if len(balanced_pool) >= DRAW_SIZE:
        for combo in combinations(balanced_pool[:16], DRAW_SIZE):
            candidates.add(tuple(combo))
            if len(candidates) >= candidate_limit // 2:
                break

    weighted_pool: list[int] = []
    for number, stats in number_stats.items():
        repeats = 1 + int(round(stats["advanced_number_score"] * 7))
        weighted_pool.extend([number] * repeats)

    while len(candidates) < candidate_limit:
        candidate = sorted(set(rng.sample(weighted_pool, min(len(weighted_pool), DRAW_SIZE * 4))))[:DRAW_SIZE]
        if len(candidate) == DRAW_SIZE:
            candidates.add(tuple(candidate))

    return [list(candidate) for candidate in sorted(candidates)]


def score_advanced_candidate(
    numbers: list[int],
    number_stats: dict[int, dict[str, Any]],
    pair_z_scores: dict[str, float],
    triple_z_scores: dict[str, float],
) -> dict[str, Any]:
    nums = sorted(numbers)
    time_decay_score = _average([number_stats[number]["time_decay_score"] for number in nums])
    bayesian_score = _average([number_stats[number]["bayesian_score"] for number in nums])
    gap_score = _average([number_stats[number]["gap_score"] for number in nums])
    stability_score = _average([number_stats[number]["frequency_stability_score"] for number in nums])
    pair_score = _pair_support(nums, pair_z_scores)
    triple_score = _triple_support(nums, triple_z_scores)
    structure = structure_balance_score(nums)
    human = human_pattern_score(nums)

    final_score = (
        time_decay_score * ADVANCED_WEIGHTS["time_decay"]
        + bayesian_score * ADVANCED_WEIGHTS["bayesian"]
        + gap_score * ADVANCED_WEIGHTS["gap"]
        + pair_score * ADVANCED_WEIGHTS["pair_significance"]
        + triple_score * ADVANCED_WEIGHTS["triple_significance"]
        + structure["structure_balance_score"] * ADVANCED_WEIGHTS["structure_balance"]
        + human["human_pattern_avoidance_score"] * ADVANCED_WEIGHTS["human_pattern_avoidance"]
        + stability_score * ADVANCED_WEIGHTS["frequency_stability"]
    )

    return {
        "numbers": nums,
        "final_score": _clamp(final_score),
        "confidence_score": _clamp(final_score) * 100.0,
        "sub_scores": {
            "time_decay_score": time_decay_score,
            "bayesian_score": bayesian_score,
            "gap_score": gap_score,
            "pair_significance_score": pair_score,
            "triple_significance_score": triple_score,
            "structure_balance_score": structure["structure_balance_score"],
            "human_pattern_avoidance_score": human["human_pattern_avoidance_score"],
            "frequency_stability_score": stability_score,
        },
        "structure_details": structure,
        "human_pattern_details": human,
        "theoretical_jackpot_odds": f"1 in {TOTAL_COMBINATIONS}",
    }


def _add_relative_probability(scored_candidates: list[dict[str, Any]], temperature: float = 0.08) -> list[dict[str, Any]]:
    if not scored_candidates:
        return scored_candidates
    max_score = max(item["final_score"] for item in scored_candidates)
    weights = [math.exp((item["final_score"] - max_score) / temperature) for item in scored_candidates]
    total_weight = sum(weights)
    for index, (item, weight) in enumerate(zip(scored_candidates, weights), start=1):
        item["relative_rank"] = index
        item["relative_top_percent"] = index / len(scored_candidates) * 100.0
        item["relative_model_probability"] = weight / total_weight if total_weight else 0.0
    return scored_candidates


def build_portfolio(scored_candidates: list[dict[str, Any]], portfolio_size: int = 10, max_overlap: int = 3) -> list[dict[str, Any]]:
    """Greedy portfolio optimizer that prefers strong tickets with low overlap."""
    portfolio: list[dict[str, Any]] = []
    for item in scored_candidates:
        numbers = set(item["numbers"])
        if all(len(numbers & set(existing["numbers"])) <= max_overlap for existing in portfolio):
            enriched = dict(item)
            enriched["portfolio_reason"] = f"selected_with_max_overlap_{max_overlap}"
            portfolio.append(enriched)
        if len(portfolio) >= portfolio_size:
            break

    if len(portfolio) < portfolio_size:
        for item in scored_candidates:
            if item not in portfolio:
                enriched = dict(item)
                enriched["portfolio_reason"] = "fallback_fill"
                portfolio.append(enriched)
            if len(portfolio) >= portfolio_size:
                break
    return portfolio


def train_advanced_ensemble_model_from_draws(
    draws: list[dict[str, Any]],
    candidate_limit: int = 18_000,
    top_limit: int = 20,
    random_seed: int = 2026,
) -> dict[str, Any]:
    number_stats = build_number_statistics(draws)
    fairness = chi_square_fairness_test(draws)
    pair_significance = build_pair_significance(draws)
    triple_significance = build_triple_significance(draws)
    candidates = generate_advanced_candidates(number_stats, candidate_limit=candidate_limit, random_seed=random_seed)

    scored_candidates = [
        score_advanced_candidate(
            candidate,
            number_stats,
            pair_significance["pair_z_scores"],
            triple_significance["triple_z_scores"],
        )
        for candidate in candidates
    ]
    scored_candidates.sort(key=lambda item: (-item["final_score"], item["numbers"]))
    scored_candidates = _add_relative_probability(scored_candidates)
    portfolio = build_portfolio(scored_candidates, portfolio_size=10, max_overlap=3)

    top_numbers = sorted(number_stats.values(), key=lambda item: (-item["advanced_number_score"], item["number"]))[:15]

    return {
        "model_name": "Advanced Statistical Ensemble Model",
        "model_version": "1.0",
        "training_draws": len(draws),
        "candidate_count": len(scored_candidates),
        "weights": ADVANCED_WEIGHTS,
        "important_note": (
            "This model ranks combinations using statistical signals. It does not change the true 6/49 jackpot odds."
        ),
        "theoretical_jackpot_odds": f"1 in {TOTAL_COMBINATIONS}",
        "fairness_test": fairness,
        "top_number_scores": top_numbers,
        "top_pair_significance": pair_significance["top_pairs"][:20],
        "top_triple_significance": triple_significance["top_triples"][:15],
        "recommended_combinations": scored_candidates[:top_limit],
        "portfolio_recommendations": portfolio,
    }


def train_advanced_ensemble_model(
    csv_path: Path = DEFAULT_DATA_PATH,
    candidate_limit: int = 18_000,
    top_limit: int = 20,
    random_seed: int = 2026,
) -> dict[str, Any]:
    return train_advanced_ensemble_model_from_draws(
        read_draws(csv_path),
        candidate_limit=candidate_limit,
        top_limit=top_limit,
        random_seed=random_seed,
    )


def save_advanced_model(model: dict[str, Any], model_path: Path = DEFAULT_MODEL_PATH) -> None:
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("w", encoding="utf-8") as file:
        json.dump(model, file, indent=2)


def load_advanced_model(model_path: Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    with Path(model_path).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_advanced_report(model: dict[str, Any], report_path: Path = DEFAULT_REPORT_PATH) -> Path:
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    fairness = model["fairness_test"]
    lines = [
        "# Advanced Statistical Ensemble Report",
        "",
        "This report combines time-decay, Bayesian smoothing, fairness checks, pair/triple significance,",
        "human-pattern avoidance, structure balance and portfolio diversification.",
        "",
        "Important: this is a statistical ranking system, not a guaranteed prediction system.",
        f"The true jackpot odds for every exact combination remain: {model['theoretical_jackpot_odds']}.",
        "",
        "## Summary",
        "",
        f"- Training draws: {model['training_draws']}",
        f"- Candidate combinations: {model['candidate_count']}",
        f"- Chi-square statistic: {fairness['chi_square']:.4f}",
        f"- Degrees of freedom: {fairness['degrees_of_freedom']}",
        f"- Approximate p-value: {fairness['p_value']:.6f}",
        f"- Fairness interpretation: {fairness['interpretation']}",
        "",
        "## Weights",
        "",
    ]
    for key, value in model["weights"].items():
        lines.append(f"- {key}: {value:.2f}")

    lines.extend(["", "## Recommended combinations", ""])
    for item in model["recommended_combinations"]:
        sub = item["sub_scores"]
        lines.extend(
            [
                f"### Rank {item['relative_rank']}: {item['numbers']}",
                "",
                f"- Confidence score: {item['confidence_score']:.2f}/100",
                f"- Relative model probability: {item['relative_model_probability']:.6%}",
                f"- Relative top percent: {item['relative_top_percent']:.2f}%",
                f"- Time-decay score: {sub['time_decay_score']:.4f}",
                f"- Bayesian score: {sub['bayesian_score']:.4f}",
                f"- Gap score: {sub['gap_score']:.4f}",
                f"- Pair significance score: {sub['pair_significance_score']:.4f}",
                f"- Triple significance score: {sub['triple_significance_score']:.4f}",
                f"- Structure balance score: {sub['structure_balance_score']:.4f}",
                f"- Human-pattern avoidance score: {sub['human_pattern_avoidance_score']:.4f}",
                "",
            ]
        )

    lines.extend(["", "## Portfolio recommendations", ""])
    for index, item in enumerate(model["portfolio_recommendations"], start=1):
        lines.append(f"- Portfolio {index}: {item['numbers']} — confidence {item['confidence_score']:.2f}/100")

    lines.extend(["", "## Top number scores", ""])
    for item in model["top_number_scores"]:
        lines.append(
            f"- {item['number']}: score={item['advanced_number_score']:.4f}, "
            f"time_decay={item['time_decay_score']:.4f}, bayesian={item['bayesian_score']:.4f}, "
            f"gap={item['gap_score']:.4f}, z={item['z_score']:.2f}"
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _matches(ticket: list[int], actual: list[int]) -> int:
    return len(set(ticket) & set(actual))


def _random_ticket(rng: random.Random) -> list[int]:
    return sorted(rng.sample(range(1, TOTAL_NUMBERS + 1), DRAW_SIZE))


def _top_ticket_by_score(number_stats: dict[int, dict[str, Any]], score_key: str) -> list[int]:
    return sorted(
        number for number, _stats in sorted(number_stats.items(), key=lambda item: (-item[1][score_key], item[0]))[:DRAW_SIZE]
    )


def run_advanced_backtest(
    csv_path: Path = DEFAULT_DATA_PATH,
    max_test_draws: int = 40,
    min_train_size: int = 300,
    candidate_limit: int = 800,
    random_seed: int = 2026,
) -> dict[str, Any]:
    """Rolling backtest that uses only past data to score the next draw."""
    draws = read_draws(csv_path)
    if len(draws) <= min_train_size:
        raise ValueError(f"Need more than {min_train_size} draws for advanced backtesting.")

    rng = random.Random(random_seed)
    start_index = max(min_train_size, len(draws) - max_test_draws)
    strategy_names = ["advanced", "time_decay", "bayesian", "gap", "frequency_stability", "random"]
    totals = {name: 0 for name in strategy_names}
    distributions = {name: Counter() for name in strategy_names}
    details = []

    for test_index in range(start_index, len(draws)):
        training_draws = draws[:test_index]
        actual_draw = draws[test_index]
        number_stats = build_number_statistics(training_draws)
        pair_significance = build_pair_significance(training_draws, top_limit=25)
        triple_significance = build_triple_significance(training_draws, top_limit=15)
        candidates = generate_advanced_candidates(number_stats, candidate_limit=candidate_limit, random_seed=random_seed + test_index)
        scored = [
            score_advanced_candidate(
                candidate,
                number_stats,
                pair_significance["pair_z_scores"],
                triple_significance["triple_z_scores"],
            )
            for candidate in candidates
        ]
        scored.sort(key=lambda item: (-item["final_score"], item["numbers"]))

        tickets = {
            "advanced": scored[0]["numbers"],
            "time_decay": _top_ticket_by_score(number_stats, "time_decay_score"),
            "bayesian": _top_ticket_by_score(number_stats, "bayesian_score"),
            "gap": _top_ticket_by_score(number_stats, "gap_score"),
            "frequency_stability": _top_ticket_by_score(number_stats, "frequency_stability_score"),
            "random": _random_ticket(rng),
        }
        detail = {
            "draw_id": actual_draw["draw_id"],
            "date": actual_draw["date"],
            "actual_numbers": actual_draw["numbers"],
            "tickets": {},
        }
        for name, ticket in tickets.items():
            match_count = _matches(ticket, actual_draw["numbers"])
            totals[name] += match_count
            distributions[name][match_count] += 1
            detail["tickets"][name] = {"numbers": ticket, "matches": match_count}
        details.append(detail)

    tested_draws = len(details)
    averages = {name: totals[name] / tested_draws for name in strategy_names}
    hit_rates = {
        name: {
            "at_least_3": sum(count for matches, count in distributions[name].items() if matches >= 3) / tested_draws,
            "at_least_4": sum(count for matches, count in distributions[name].items() if matches >= 4) / tested_draws,
        }
        for name in strategy_names
    }

    best_strategy = max(averages, key=lambda name: averages[name])
    conclusion = (
        f"Най-добрата стратегия по средни съвпадения в историческата проверка е: {_bg_strategy_name(best_strategy)}. "
        "Това е проверка на модела, не доказателство, че бъдещи тегления са предсказуеми."
    )

    return {
        "tested_draws": tested_draws,
        "min_train_size": min_train_size,
        "candidate_limit": candidate_limit,
        "random_seed": random_seed,
        "averages": averages,
        "hit_rates": hit_rates,
        "distributions": {name: {str(k): distributions[name][k] for k in range(DRAW_SIZE + 1)} for name in strategy_names},
        "best_strategy": best_strategy,
        "conclusion": conclusion,
        "details": details,
    }



def _bg_strategy_name(name: str) -> str:
    labels = {
        "advanced": "Разширен ансамбъл",
        "time_decay": "Времево затихване",
        "bayesian": "Бейсово изглаждане",
        "gap": "Интервален модел",
        "frequency_stability": "Честотна стабилност",
        "random": "Случаен базов модел",
    }
    return labels.get(str(name), str(name).replace("_", " "))


def save_advanced_backtest(backtest: dict[str, Any], path: Path = DEFAULT_BACKTEST_JSON_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(backtest, file, indent=2)


def load_advanced_backtest(path: Path = DEFAULT_BACKTEST_JSON_PATH) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_advanced_backtest_report(backtest: dict[str, Any], report_path: Path = DEFAULT_BACKTEST_REPORT_PATH) -> Path:
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    best_label = _bg_strategy_name(backtest.get("best_strategy", ""))
    lines = [
        "# Отчет от историческа проверка",
        "",
        "Историческата проверка тества модела назад във времето: при всяка стъпка се използват само предишни тиражи и се сравнява с реалния следващ тираж.",
        "",
        f"- Тествани тиражи: {backtest['tested_draws']}",
        f"- Минимален обучаващ период: {backtest['min_train_size']}",
        f"- Кандидат-комбинации на стъпка: {backtest['candidate_limit']}",
        f"- Най-добра стратегия: {best_label}",
        "",
        backtest["conclusion"],
        "",
        "## Средни съвпадения",
        "",
        "| Стратегия | Средни съвпадения | >=3 съвпадения | >=4 съвпадения |",
        "|:---|---:|---:|---:|",
    ]
    for name, average in backtest["averages"].items():
        lines.append(
            f"| {_bg_strategy_name(name)} | {average:.4f} | "
            f"{backtest['hit_rates'][name]['at_least_3']:.2%} | "
            f"{backtest['hit_rates'][name]['at_least_4']:.2%} |"
        )

    lines.extend(["", "## Разпределение на съвпаденията", "", "| Стратегия | 0 | 1 | 2 | 3 | 4 | 5 | 6 |", "|:---|---:|---:|---:|---:|---:|---:|---:|"])
    for name, distribution in backtest["distributions"].items():
        lines.append("| " + _bg_strategy_name(name) + " | " + " | ".join(str(distribution[str(i)]) for i in range(DRAW_SIZE + 1)) + " |")

    lines.extend(["", "## Последни тествани тиражи", ""])
    for item in backtest["details"][-30:]:
        advanced = item["tickets"]["advanced"]
        random_ticket = item["tickets"]["random"]
        lines.append(
            f"- Тираж {item['draw_id']} ({item['date']}): реални={item['actual_numbers']}, "
            f"разширен модел={advanced['numbers']} ({advanced['matches']} съвпадения), "
            f"случаен фиш={random_ticket['numbers']} ({random_ticket['matches']} съвпадения)"
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
