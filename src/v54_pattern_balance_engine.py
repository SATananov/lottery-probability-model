from __future__ import annotations

import re
from collections import Counter
from typing import Any


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_TICKET = 6


def parse_combination_lines(text: str) -> list[list[int]]:
    combinations: list[list[int]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        numbers = [int(value) for value in re.findall(r"\d+", line)]
        if numbers:
            combinations.append(numbers)

    return combinations


def validate_combination(combo: list[int]) -> list[str]:
    errors: list[str] = []

    if len(combo) != NUMBERS_PER_TICKET:
        errors.append("Комбинацията трябва да съдържа точно 6 числа.")

    if any(number < MIN_NUMBER or number > MAX_NUMBER for number in combo):
        errors.append("Всички числа трябва да са между 1 и 49.")

    if len(set(combo)) != len(combo):
        errors.append("Комбинацията съдържа повтарящи се числа.")

    return errors


def _range_name(number: int) -> str:
    if 1 <= number <= 9:
        return "1-9"
    if 10 <= number <= 19:
        return "10-19"
    if 20 <= number <= 29:
        return "20-29"
    if 30 <= number <= 39:
        return "30-39"
    return "40-49"


def _score_band(score: float) -> str:
    if score >= 80:
        return "Отличен баланс"
    if score >= 65:
        return "Добър баланс"
    if score >= 45:
        return "Среден баланс"
    return "Небалансирана структура"


def _sum_band(total_sum: int) -> str:
    if 115 <= total_sum <= 185:
        return "Балансирана сума"
    if 95 <= total_sum < 115:
        return "По-ниска сума"
    if 185 < total_sum <= 210:
        return "По-висока сума"
    if total_sum < 95:
        return "Много ниска сума"
    return "Много висока сума"


def _longest_consecutive_run(numbers: list[int]) -> int:
    if not numbers:
        return 0

    longest = 1
    current = 1

    for left, right in zip(numbers, numbers[1:]):
        if right == left + 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def _consecutive_pairs(numbers: list[int]) -> int:
    return sum(1 for left, right in zip(numbers, numbers[1:]) if right == left + 1)


def _pattern_warnings_and_recommendations(metrics: dict[str, Any]) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    recommendations: list[str] = []

    odd_count = metrics["odd_count"]
    even_count = metrics["even_count"]
    low_count = metrics["low_count"]
    high_count = metrics["high_count"]
    total_sum = metrics["sum"]
    longest_run = metrics["longest_consecutive_run"]
    consecutive_pairs = metrics["consecutive_pairs"]
    max_same_final_digit = metrics["max_same_final_digit_count"]
    min_gap = metrics["min_gap"]
    max_gap = metrics["max_gap"]
    range_count_used = metrics["range_count_used"]

    if odd_count in {0, 1, 5, 6} or even_count in {0, 1, 5, 6}:
        warnings.append("Комбинацията има силно изместен баланс между четни и нечетни числа.")
        recommendations.append("По-балансиран вариант често е 2/4, 3/3 или 4/2 между четни и нечетни.")

    if low_count in {0, 1, 5, 6} or high_count in {0, 1, 5, 6}:
        warnings.append("Комбинацията е силно концентрирана само в ниски или само във високи числа.")
        recommendations.append("Помисли за по-добро разпределение между 1-24 и 25-49.")

    if total_sum < 95:
        warnings.append("Сумата на числата е много ниска спрямо нормален балансиран профил.")
        recommendations.append("Добави едно или две по-високи числа, ако целиш по-неутрален профил.")

    if total_sum > 210:
        warnings.append("Сумата на числата е много висока спрямо нормален балансиран профил.")
        recommendations.append("Добави едно или две по-ниски числа, ако целиш по-неутрален профил.")

    if longest_run >= 4:
        warnings.append("Има дълга последователност от числа.")
        recommendations.append("Намали дългите поредици, ако искаш по-естествено разпръсната структура.")
    elif consecutive_pairs >= 2:
        warnings.append("Има няколко последователни двойки.")
        recommendations.append("Провери дали поредиците не правят комбинацията прекалено подредена.")

    if max_same_final_digit >= 3:
        warnings.append("Няколко числа завършват на една и съща цифра.")
        recommendations.append("Разнообрази крайните цифри, ако искаш по-балансирана комбинация.")

    if min_gap == 1 and max_gap <= 7:
        warnings.append("Комбинацията е доста компактна и числата са близо едно до друго.")
        recommendations.append("Добави по-раздалечени числа, ако целиш по-широко покритие.")

    if max_gap >= 25:
        warnings.append("Има много голямо разстояние между две съседни избрани числа.")
        recommendations.append("Провери дали комбинацията не е прекалено разкъсана.")

    if range_count_used <= 2:
        warnings.append("Числата са концентрирани в твърде малко диапазони.")
        recommendations.append("Разпредели числата в повече диапазони: 1-9, 10-19, 20-29, 30-39, 40-49.")

    if not warnings:
        warnings.append("Не са открити сериозни структурни проблеми.")
    if not recommendations:
        recommendations.append("Комбинацията има приемлив структурен баланс. Сравни я и с покритието на фиша.")

    return warnings, recommendations


def analyze_combination_pattern(combo: list[int], index: int = 1) -> dict[str, Any]:
    errors = validate_combination(combo)

    if errors:
        return {
            "ticket_index": index,
            "combination": combo,
            "combination_text": ", ".join(str(number) for number in combo),
            "is_valid": False,
            "status": " ".join(errors),
            "pattern_score": 0.0,
            "band": "Невалидна комбинация",
            "warnings": errors,
            "recommendations": ["Поправи комбинацията и я анализирай отново."],
        }

    numbers = sorted(int(number) for number in combo)
    total_sum = sum(numbers)

    odd_count = sum(1 for number in numbers if number % 2 == 1)
    even_count = NUMBERS_PER_TICKET - odd_count

    low_count = sum(1 for number in numbers if number <= 24)
    high_count = NUMBERS_PER_TICKET - low_count

    gaps = [right - left for left, right in zip(numbers, numbers[1:])]
    min_gap = min(gaps) if gaps else 0
    max_gap = max(gaps) if gaps else 0
    average_gap = sum(gaps) / len(gaps) if gaps else 0.0

    range_distribution = Counter(_range_name(number) for number in numbers)
    final_digit_distribution = Counter(number % 10 for number in numbers)

    longest_run = _longest_consecutive_run(numbers)
    consecutive_pairs = _consecutive_pairs(numbers)
    max_same_final_digit_count = max(final_digit_distribution.values()) if final_digit_distribution else 0
    range_count_used = sum(1 for value in range_distribution.values() if value > 0)

    metrics: dict[str, Any] = {
        "ticket_index": index,
        "combination": numbers,
        "combination_text": ", ".join(str(number) for number in numbers),
        "is_valid": True,
        "status": "Валидна",
        "sum": total_sum,
        "sum_band": _sum_band(total_sum),
        "odd_count": odd_count,
        "even_count": even_count,
        "low_count": low_count,
        "high_count": high_count,
        "gaps": gaps,
        "min_gap": min_gap,
        "max_gap": max_gap,
        "average_gap": round(average_gap, 2),
        "longest_consecutive_run": longest_run,
        "consecutive_pairs": consecutive_pairs,
        "max_same_final_digit_count": max_same_final_digit_count,
        "range_count_used": range_count_used,
        "range_distribution": {
            "1-9": range_distribution.get("1-9", 0),
            "10-19": range_distribution.get("10-19", 0),
            "20-29": range_distribution.get("20-29", 0),
            "30-39": range_distribution.get("30-39", 0),
            "40-49": range_distribution.get("40-49", 0),
        },
        "final_digit_distribution": {
            str(digit): final_digit_distribution.get(digit, 0)
            for digit in range(10)
        },
    }

    score = 100.0

    # Odd/even balance
    if odd_count in {0, 6}:
        score -= 25
    elif odd_count in {1, 5}:
        score -= 14
    elif odd_count in {2, 4}:
        score -= 3

    # Low/high balance
    if low_count in {0, 6}:
        score -= 25
    elif low_count in {1, 5}:
        score -= 14
    elif low_count in {2, 4}:
        score -= 3

    # Sum profile
    if total_sum < 80 or total_sum > 230:
        score -= 24
    elif total_sum < 95 or total_sum > 210:
        score -= 15
    elif total_sum < 115 or total_sum > 185:
        score -= 6

    # Consecutive structure
    if longest_run >= 5:
        score -= 25
    elif longest_run == 4:
        score -= 18
    elif longest_run == 3:
        score -= 8

    if consecutive_pairs >= 3:
        score -= 12
    elif consecutive_pairs == 2:
        score -= 6

    # Gap structure
    if max_gap >= 30:
        score -= 14
    elif max_gap >= 25:
        score -= 8

    if max_gap <= 8:
        score -= 10

    if min_gap == 1:
        score -= 4

    # Range diversity
    if range_count_used <= 2:
        score -= 14
    elif range_count_used == 3:
        score -= 4

    # Final digit repetition
    if max_same_final_digit_count >= 4:
        score -= 18
    elif max_same_final_digit_count == 3:
        score -= 8

    score = max(0.0, min(100.0, round(score, 2)))

    metrics["pattern_score"] = score
    metrics["band"] = _score_band(score)

    warnings, recommendations = _pattern_warnings_and_recommendations(metrics)
    metrics["warnings"] = warnings
    metrics["recommendations"] = recommendations

    return metrics


def analyze_pattern_balance(combinations_input: list[list[int]]) -> dict[str, Any]:
    rows = [
        analyze_combination_pattern(combo, index=index)
        for index, combo in enumerate(combinations_input, start=1)
    ]

    valid_rows = [row for row in rows if row.get("is_valid")]
    invalid_count = len(rows) - len(valid_rows)

    if valid_rows:
        average_score = round(
            sum(float(row["pattern_score"]) for row in valid_rows) / len(valid_rows),
            2,
        )
    else:
        average_score = 0.0

    aggregate_ranges = Counter()
    aggregate_final_digits = Counter()
    aggregate_odd = 0
    aggregate_even = 0
    aggregate_low = 0
    aggregate_high = 0
    aggregate_sum = 0

    for row in valid_rows:
        aggregate_odd += int(row["odd_count"])
        aggregate_even += int(row["even_count"])
        aggregate_low += int(row["low_count"])
        aggregate_high += int(row["high_count"])
        aggregate_sum += int(row["sum"])

        for key, value in row["range_distribution"].items():
            aggregate_ranges[key] += int(value)

        for key, value in row["final_digit_distribution"].items():
            aggregate_final_digits[key] += int(value)

    portfolio_warnings: list[str] = []
    portfolio_recommendations: list[str] = []

    weak_rows = [row for row in valid_rows if float(row["pattern_score"]) < 45]
    medium_rows = [row for row in valid_rows if 45 <= float(row["pattern_score"]) < 65]

    if invalid_count:
        portfolio_warnings.append(f"{invalid_count} невалидни комбинации са изключени от общата оценка.")

    if not valid_rows:
        portfolio_warnings.append("Няма валидни комбинации за анализ.")
        portfolio_recommendations.append("Въведи поне една валидна комбинация с 6 различни числа между 1 и 49.")

    if weak_rows:
        portfolio_warnings.append("Има комбинации с небалансирана структура.")
        portfolio_recommendations.append("Прегледай комбинациите с най-ниска оценка и коригирай крайностите.")

    if medium_rows and not weak_rows:
        portfolio_warnings.append("Има комбинации със среден баланс.")
        portfolio_recommendations.append("Можеш да подобриш фиша чрез по-добро разпределение по диапазони, сума и четни/нечетни.")

    if valid_rows and not portfolio_warnings:
        portfolio_warnings.append("Общият структурен баланс изглежда стабилен.")

    if valid_rows and not portfolio_recommendations:
        portfolio_recommendations.append("Фишът има добър структурен профил. Провери го и през покритието на фиша.")

    return {
        "valid_count": len(valid_rows),
        "invalid_count": invalid_count,
        "average_pattern_score": average_score,
        "band": _score_band(average_score),
        "rows": rows,
        "portfolio_warnings": portfolio_warnings,
        "portfolio_recommendations": portfolio_recommendations,
        "aggregate": {
            "total_sum": aggregate_sum,
            "average_sum": round(aggregate_sum / len(valid_rows), 2) if valid_rows else 0.0,
            "odd_even_distribution": {
                "odd": aggregate_odd,
                "even": aggregate_even,
            },
            "low_high_distribution": {
                "low_1_24": aggregate_low,
                "high_25_49": aggregate_high,
            },
            "range_distribution": {
                "1-9": aggregate_ranges.get("1-9", 0),
                "10-19": aggregate_ranges.get("10-19", 0),
                "20-29": aggregate_ranges.get("20-29", 0),
                "30-39": aggregate_ranges.get("30-39", 0),
                "40-49": aggregate_ranges.get("40-49", 0),
            },
            "final_digit_distribution": {
                str(digit): aggregate_final_digits.get(str(digit), 0)
                for digit in range(10)
            },
        },
    }
