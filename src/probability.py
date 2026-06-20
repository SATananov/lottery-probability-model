from math import comb


TOTAL_NUMBERS = 49
DRAW_COUNT = 6


def get_total_combinations() -> int:
    """
    Calculate the total number of possible 6/49 lottery combinations.
    """
    return comb(TOTAL_NUMBERS, DRAW_COUNT)


def get_jackpot_probability() -> dict:
    """
    Calculate the probability of matching all 6 numbers.
    """
    total_combinations = get_total_combinations()
    probability = 1 / total_combinations

    return {
        "total_combinations": total_combinations,
        "probability_decimal": probability,
        "probability_percent": probability * 100,
        "odds": f"1 in {total_combinations}",
    }


def get_exact_match_probability(matches: int) -> dict:
    """
    Calculate the probability of matching exactly a given number of numbers.
    """
    if matches < 0 or matches > DRAW_COUNT:
        raise ValueError("Matches must be between 0 and 6.")

    favorable_combinations = (
        comb(DRAW_COUNT, matches)
        * comb(TOTAL_NUMBERS - DRAW_COUNT, DRAW_COUNT - matches)
    )

    total_combinations = get_total_combinations()
    probability = favorable_combinations / total_combinations

    return {
        "matches": matches,
        "favorable_combinations": favorable_combinations,
        "total_combinations": total_combinations,
        "probability_decimal": probability,
        "probability_percent": probability * 100,
        "odds": f"1 in {round(1 / probability)}" if probability > 0 else "Impossible",
    }
