from random import sample


TOTAL_NUMBERS = 49
DRAW_COUNT = 6


def generate_random_combination() -> list[int]:
    """
    Generate one random 6/49 lottery combination.
    """
    return sorted(sample(range(1, TOTAL_NUMBERS + 1), DRAW_COUNT))


def validate_ticket(ticket: list[int]) -> bool:
    """
    Validate whether a ticket is a correct 6/49 combination.

    A valid ticket must contain exactly 6 unique numbers
    between 1 and 49.
    """
    if len(ticket) != DRAW_COUNT:
        return False

    if len(set(ticket)) != DRAW_COUNT:
        return False

    return all(1 <= number <= TOTAL_NUMBERS for number in ticket)
