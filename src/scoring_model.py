from src.historical_analysis import (
    calculate_number_frequencies,
    calculate_recency_gaps,
)


def score_numbers(
    draws: list[dict],
    frequency_weight: float = 0.6,
    gap_weight: float = 0.4,
) -> dict[int, float]:
    """
    Score numbers using a simple training baseline model.

    The score combines:
    - historical frequency
    - recency gap

    This is not a true prediction model. It is only a transparent
    baseline for learning how scoring models work.
    """
    if not draws:
        return {}

    frequencies = calculate_number_frequencies(draws)
    gaps = calculate_recency_gaps(draws)

    max_frequency = max(frequencies.values()) or 1
    max_gap = max(gaps.values()) or 1

    scores = {}

    for number in frequencies:
        frequency_score = frequencies[number] / max_frequency
        gap_score = gaps[number] / max_gap

        scores[number] = (
            frequency_weight * frequency_score
            + gap_weight * gap_score
        )

    return scores


def get_top_scored_numbers(
    draws: list[dict],
    limit: int = 10,
) -> list[tuple[int, float]]:
    """
    Return the numbers with the highest training baseline score.
    """
    scores = score_numbers(draws)

    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]


def generate_scored_combination(draws: list[dict]) -> list[int]:
    """
    Generate one 6-number training combination from the top scored numbers.
    """
    top_numbers = get_top_scored_numbers(draws, limit=6)
    return sorted(number for number, _score in top_numbers)
