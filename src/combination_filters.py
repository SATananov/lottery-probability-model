from collections import Counter
from math import exp


LOW_HIGH_SPLIT = 24
DECADE_BUCKETS = [
    (1, 9),
    (10, 19),
    (20, 29),
    (30, 39),
    (40, 49),
]


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """
    Keep a score inside a controlled range.
    """
    return max(minimum, min(maximum, value))


def combination_sum(numbers: list[int]) -> int:
    """
    Return the total sum of a lottery combination.
    """
    return sum(numbers)


def count_even_odd(numbers: list[int]) -> tuple[int, int]:
    """
    Count even and odd numbers in a combination.
    """
    even_count = sum(1 for number in numbers if number % 2 == 0)
    odd_count = len(numbers) - even_count
    return even_count, odd_count


def count_low_high(numbers: list[int]) -> tuple[int, int]:
    """
    Count low and high numbers in a combination.

    Low numbers are 1-24. High numbers are 25-49.
    """
    low_count = sum(1 for number in numbers if number <= LOW_HIGH_SPLIT)
    high_count = len(numbers) - low_count
    return low_count, high_count


def count_consecutive_pairs(numbers: list[int]) -> int:
    """
    Count adjacent consecutive pairs in a sorted combination.

    Example: [7, 8, 9, 22, 34, 41] has two consecutive pairs:
    7-8 and 8-9.
    """
    sorted_numbers = sorted(numbers)
    return sum(
        1
        for left, right in zip(sorted_numbers, sorted_numbers[1:])
        if right - left == 1
    )


def decade_bucket_counts(numbers: list[int]) -> dict[str, int]:
    """
    Count how many numbers fall in each decade-like bucket.
    """
    counts = {}

    for start, end in DECADE_BUCKETS:
        label = f"{start}-{end}"
        counts[label] = sum(1 for number in numbers if start <= number <= end)

    return counts


def max_same_last_digit_count(numbers: list[int]) -> int:
    """
    Return the maximum count of numbers sharing the same last digit.
    """
    counter = Counter(number % 10 for number in numbers)
    return max(counter.values()) if counter else 0


def calculate_historical_structure_profile(draws: list[dict]) -> dict:
    """
    Learn typical combination structure from historical draws.
    """
    if not draws:
        raise ValueError("Cannot build structure profile without historical draws.")

    sums = [combination_sum(draw["numbers"]) for draw in draws]
    mean_sum = sum(sums) / len(sums)

    if len(sums) > 1:
        variance = sum((value - mean_sum) ** 2 for value in sums) / (len(sums) - 1)
        std_sum = variance ** 0.5
    else:
        std_sum = 35.0

    even_odd_counter = Counter(count_even_odd(draw["numbers"]) for draw in draws)
    low_high_counter = Counter(count_low_high(draw["numbers"]) for draw in draws)
    consecutive_counter = Counter(count_consecutive_pairs(draw["numbers"]) for draw in draws)

    bucket_diversity_values = []
    max_bucket_values = []
    last_digit_max_values = []

    for draw in draws:
        bucket_counts = decade_bucket_counts(draw["numbers"])
        used_buckets = sum(1 for count in bucket_counts.values() if count > 0)
        max_bucket_count = max(bucket_counts.values())
        bucket_diversity_values.append(used_buckets)
        max_bucket_values.append(max_bucket_count)
        last_digit_max_values.append(max_same_last_digit_count(draw["numbers"]))

    return {
        "mean_sum": mean_sum,
        "std_sum": max(std_sum, 1.0),
        "even_odd_distribution": even_odd_counter,
        "low_high_distribution": low_high_counter,
        "consecutive_distribution": consecutive_counter,
        "average_bucket_diversity": sum(bucket_diversity_values) / len(bucket_diversity_values),
        "average_max_bucket_count": sum(max_bucket_values) / len(max_bucket_values),
        "average_max_last_digit_count": sum(last_digit_max_values) / len(last_digit_max_values),
    }


def _distribution_score(observed_key: tuple[int, int] | int, distribution: Counter) -> float:
    """
    Score a structural pattern by how often it appeared historically.
    """
    total = sum(distribution.values())
    if total == 0:
        return 0.5

    raw_frequency = distribution.get(observed_key, 0) / total

    # Smooth the value so rare but possible patterns are not punished too hard
    # on small training datasets.
    return clamp(0.35 + raw_frequency * 1.30)


def score_combination_structure(numbers: list[int], profile: dict) -> dict:
    """
    Score a candidate combination by structural similarity to historical draws.
    """
    sorted_numbers = sorted(numbers)
    total_sum = combination_sum(sorted_numbers)
    even_odd = count_even_odd(sorted_numbers)
    low_high = count_low_high(sorted_numbers)
    consecutive_pairs = count_consecutive_pairs(sorted_numbers)
    bucket_counts = decade_bucket_counts(sorted_numbers)
    used_buckets = sum(1 for count in bucket_counts.values() if count > 0)
    max_bucket_count = max(bucket_counts.values())
    max_last_digit_count = max_same_last_digit_count(sorted_numbers)

    sum_distance = abs(total_sum - profile["mean_sum"])
    sum_score = exp(-sum_distance / (profile["std_sum"] * 1.75))

    even_odd_score = _distribution_score(
        even_odd,
        profile["even_odd_distribution"],
    )
    low_high_score = _distribution_score(
        low_high,
        profile["low_high_distribution"],
    )
    consecutive_score = _distribution_score(
        consecutive_pairs,
        profile["consecutive_distribution"],
    )

    bucket_diversity_score = clamp(used_buckets / 5)
    if max_bucket_count <= 2:
        bucket_concentration_score = 1.0
    elif max_bucket_count == 3:
        bucket_concentration_score = 0.70
    else:
        bucket_concentration_score = 0.35

    if max_last_digit_count <= 2:
        last_digit_score = 1.0
    elif max_last_digit_count == 3:
        last_digit_score = 0.65
    else:
        last_digit_score = 0.30

    structure_score = (
        sum_score * 0.25
        + even_odd_score * 0.15
        + low_high_score * 0.15
        + consecutive_score * 0.15
        + bucket_diversity_score * 0.10
        + bucket_concentration_score * 0.10
        + last_digit_score * 0.10
    )

    return {
        "sum": total_sum,
        "even_count": even_odd[0],
        "odd_count": even_odd[1],
        "low_count": low_high[0],
        "high_count": low_high[1],
        "consecutive_pairs": consecutive_pairs,
        "used_decade_buckets": used_buckets,
        "max_bucket_count": max_bucket_count,
        "max_same_last_digit_count": max_last_digit_count,
        "sum_score": clamp(sum_score),
        "even_odd_score": even_odd_score,
        "low_high_score": low_high_score,
        "consecutive_score": consecutive_score,
        "bucket_score": clamp((bucket_diversity_score + bucket_concentration_score) / 2),
        "last_digit_score": last_digit_score,
        "structure_score": clamp(structure_score),
    }
