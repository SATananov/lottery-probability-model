from src.generator import generate_random_combination, validate_ticket


def count_matches(ticket: list[int], draw: list[int]) -> int:
    """
    Count how many numbers from the ticket match the draw.
    """
    return len(set(ticket) & set(draw))


def simulate_ticket(ticket: list[int], simulations: int = 100_000) -> dict:
    """
    Simulate many lottery draws and count the match results.
    """
    if not validate_ticket(ticket):
        raise ValueError("Invalid ticket. Use 6 unique numbers between 1 and 49.")

    results = {matches: 0 for matches in range(7)}

    for _ in range(simulations):
        draw = generate_random_combination()
        matches = count_matches(ticket, draw)
        results[matches] += 1

    return {
        "ticket": sorted(ticket),
        "simulations": simulations,
        "results": results,
    }
