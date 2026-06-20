from collections import Counter


TOTAL_NUMBERS = 49
DRAW_COUNT = 6


def _frequency_map(draws: list[dict]) -> dict[int, float]:
    """
    Return appearance frequency per number for a set of draws.
    """
    counts = Counter()

    for draw in draws:
        counts.update(draw["numbers"])

    if not draws:
        return {number: 0.0 for number in range(1, TOTAL_NUMBERS + 1)}

    return {
        number: counts[number] / len(draws)
        for number in range(1, TOTAL_NUMBERS + 1)
    }


def build_rolling_window_scores(
    draws: list[dict],
    windows: tuple[int, ...] = (10, 25, 50, 100),
) -> dict[int, dict]:
    """
    Build short-term and long-term frequency information for each number.
    """
    full_history = _frequency_map(draws)
    available_windows = [window for window in windows if len(draws) >= window]

    if not available_windows:
        available_windows = [len(draws)] if draws else []

    window_maps = {
        window: _frequency_map(draws[-window:])
        for window in available_windows
        if window > 0
    }

    baseline = DRAW_COUNT / TOTAL_NUMBERS
    scores = {}

    for number in range(1, TOTAL_NUMBERS + 1):
        recent_values = [window_map[number] for window_map in window_maps.values()]
        recent_average = sum(recent_values) / len(recent_values) if recent_values else 0.0
        long_term = full_history[number]

        trend = recent_average - long_term
        balanced_recent_score = 1.0 - min(1.0, abs(recent_average - baseline) / baseline)
        activity_score = min(1.0, recent_average / baseline) if baseline > 0 else 0.0

        rolling_score = (
            balanced_recent_score * 0.45
            + activity_score * 0.35
            + (0.50 + max(-0.50, min(0.50, trend / baseline if baseline else 0.0))) * 0.20
        )

        scores[number] = {
            "long_term_frequency": long_term,
            "recent_average_frequency": recent_average,
            "trend_vs_long_term": trend,
            "rolling_score": max(0.0, min(1.0, rolling_score)),
        }

    return scores


def score_combination_rolling(numbers: list[int], rolling_scores: dict[int, dict]) -> dict:
    """
    Score a combination by rolling-window behavior.
    """
    if not numbers:
        return {"rolling_score": 0.0, "average_recent_frequency": 0.0}

    values = [rolling_scores[number]["rolling_score"] for number in numbers]
    recent_values = [rolling_scores[number]["recent_average_frequency"] for number in numbers]

    return {
        "rolling_score": sum(values) / len(values),
        "average_recent_frequency": sum(recent_values) / len(recent_values),
    }
