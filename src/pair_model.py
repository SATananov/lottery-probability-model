from collections import Counter
from itertools import combinations


def build_pair_counts(draws: list[dict]) -> Counter:
    """
    Count how often each unordered pair of numbers appears together.
    """
    pair_counter = Counter()

    for draw in draws:
        for pair in combinations(sorted(draw["numbers"]), 2):
            pair_counter[pair] += 1

    return pair_counter


def build_triple_counts(draws: list[dict]) -> Counter:
    """
    Count how often each unordered triple of numbers appears together.
    """
    triple_counter = Counter()

    for draw in draws:
        for triple in combinations(sorted(draw["numbers"]), 3):
            triple_counter[triple] += 1

    return triple_counter


def score_pair_support(numbers: list[int], pair_counts: Counter) -> dict:
    """
    Score a combination by historical pair co-occurrence support.
    """
    pairs = list(combinations(sorted(numbers), 2))

    if not pairs or not pair_counts:
        return {
            "pair_score": 0.0,
            "pair_total_support": 0,
            "pair_average_support": 0.0,
            "strong_pairs": [],
        }

    max_pair_count = max(pair_counts.values()) if pair_counts else 1
    pair_values = [pair_counts.get(pair, 0) for pair in pairs]
    total_support = sum(pair_values)
    average_support = total_support / len(pairs)
    pair_score = average_support / max_pair_count if max_pair_count > 0 else 0.0

    strong_pairs = sorted(
        [
            {"pair": list(pair), "count": pair_counts.get(pair, 0)}
            for pair in pairs
            if pair_counts.get(pair, 0) > 0
        ],
        key=lambda item: (-item["count"], item["pair"]),
    )[:5]

    return {
        "pair_score": max(0.0, min(1.0, pair_score)),
        "pair_total_support": total_support,
        "pair_average_support": average_support,
        "strong_pairs": strong_pairs,
    }


def score_triple_support(numbers: list[int], triple_counts: Counter) -> dict:
    """
    Score a combination by historical triple co-occurrence support.

    Triple support is intentionally weighted lightly in the combined model because
    triples are sparse and can overfit small datasets.
    """
    triples = list(combinations(sorted(numbers), 3))

    if not triples or not triple_counts:
        return {
            "triple_score": 0.0,
            "triple_total_support": 0,
            "strong_triples": [],
        }

    max_triple_count = max(triple_counts.values()) if triple_counts else 1
    triple_values = [triple_counts.get(triple, 0) for triple in triples]
    total_support = sum(triple_values)
    average_support = total_support / len(triples)
    triple_score = average_support / max_triple_count if max_triple_count > 0 else 0.0

    strong_triples = sorted(
        [
            {"triple": list(triple), "count": triple_counts.get(triple, 0)}
            for triple in triples
            if triple_counts.get(triple, 0) > 0
        ],
        key=lambda item: (-item["count"], item["triple"]),
    )[:5]

    return {
        "triple_score": max(0.0, min(1.0, triple_score)),
        "triple_total_support": total_support,
        "strong_triples": strong_triples,
    }
