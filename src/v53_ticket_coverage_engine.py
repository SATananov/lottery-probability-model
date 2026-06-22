from __future__ import annotations

import re
from collections import Counter
from itertools import combinations
from typing import Any


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_TICKET = 6


def parse_ticket_lines(text: str) -> list[list[int]]:
    tickets: list[list[int]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        numbers = [int(value) for value in re.findall(r"\d+", line)]
        if numbers:
            tickets.append(numbers)

    return tickets


def validate_combination(combo: list[int]) -> list[str]:
    errors: list[str] = []

    if len(combo) != NUMBERS_PER_TICKET:
        errors.append("Комбинацията трябва да съдържа точно 6 числа.")

    out_of_range = [number for number in combo if number < MIN_NUMBER or number > MAX_NUMBER]
    if out_of_range:
        errors.append("Всички числа трябва да са между 1 и 49.")

    if len(set(combo)) != len(combo):
        errors.append("Комбинацията съдържа повтарящи се числа.")

    return errors


def _sorted_ticket(combo: list[int]) -> list[int]:
    return sorted(int(number) for number in combo)


def _pair_counter(tickets: list[list[int]]) -> Counter[tuple[int, int]]:
    counter: Counter[tuple[int, int]] = Counter()

    for ticket in tickets:
        for pair in combinations(sorted(ticket), 2):
            counter[pair] += 1

    return counter


def _triple_counter(tickets: list[list[int]]) -> Counter[tuple[int, int, int]]:
    counter: Counter[tuple[int, int, int]] = Counter()

    for ticket in tickets:
        for triple in combinations(sorted(ticket), 3):
            counter[triple] += 1

    return counter


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
        return "Отлично покритие"
    if score >= 65:
        return "Добро покритие"
    if score >= 45:
        return "Средно покритие"
    return "Прекалено концентриран фиш"


def analyze_ticket_coverage(combinations_input: list[list[int]]) -> dict[str, Any]:
    validation_rows: list[dict[str, Any]] = []
    valid_tickets: list[list[int]] = []

    for index, combo in enumerate(combinations_input, start=1):
        clean_combo = [int(number) for number in combo]
        errors = validate_combination(clean_combo)
        sorted_combo = _sorted_ticket(clean_combo) if not errors else clean_combo

        validation_rows.append(
            {
                "ticket_index": index,
                "combination": sorted_combo,
                "combination_text": ", ".join(str(number) for number in sorted_combo),
                "is_valid": not errors,
                "status": "Валидна" if not errors else " ".join(errors),
            }
        )

        if not errors:
            valid_tickets.append(sorted_combo)

    ticket_count = len(valid_tickets)
    invalid_count = len(combinations_input) - ticket_count
    total_slots = ticket_count * NUMBERS_PER_TICKET

    unique_numbers = sorted({number for ticket in valid_tickets for number in ticket})
    unique_count = len(unique_numbers)
    max_possible_unique = min(MAX_NUMBER, total_slots) if total_slots else 0
    coverage_efficiency = unique_count / max_possible_unique if max_possible_unique else 0.0
    unique_coverage_49 = unique_count / MAX_NUMBER if MAX_NUMBER else 0.0

    duplicate_counter = Counter(tuple(ticket) for ticket in valid_tickets)
    duplicate_tickets = sum(count - 1 for count in duplicate_counter.values() if count > 1)

    overlaps: list[int] = []
    for left, right in combinations(valid_tickets, 2):
        overlaps.append(len(set(left).intersection(right)))

    average_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0
    maximum_overlap = max(overlaps) if overlaps else 0

    pairs = _pair_counter(valid_tickets)
    triples = _triple_counter(valid_tickets)

    repeated_pairs = {pair: count for pair, count in pairs.items() if count > 1}
    repeated_triples = {triple: count for triple, count in triples.items() if count > 1}

    odd_count = sum(1 for ticket in valid_tickets for number in ticket if number % 2 == 1)
    even_count = total_slots - odd_count

    low_count = sum(1 for ticket in valid_tickets for number in ticket if number <= 24)
    high_count = total_slots - low_count

    range_distribution = Counter(_range_name(number) for ticket in valid_tickets for number in ticket)

    score = 100.0

    if ticket_count == 0:
        score = 0.0
    elif ticket_count == 1:
        score -= 25.0

    score -= duplicate_tickets * 25.0
    score -= min(30.0, average_overlap * 12.0)

    if maximum_overlap >= 5:
        score -= 30.0
    elif maximum_overlap == 4:
        score -= 20.0
    elif maximum_overlap == 3:
        score -= 8.0

    score -= min(18.0, len(repeated_pairs) * 1.2)
    score -= min(28.0, len(repeated_triples) * 4.0)

    if coverage_efficiency < 0.70:
        score -= (0.70 - coverage_efficiency) * 45.0

    score = max(0.0, min(100.0, round(score, 2)))

    warnings: list[str] = []
    recommendations: list[str] = []

    if invalid_count:
        warnings.append(f"{invalid_count} невалидни комбинации са изключени от изчисленията.")

    if ticket_count == 0:
        warnings.append("Няма валидни комбинации за анализ.")
        recommendations.append("Въведи поне две валидни комбинации с по 6 различни числа между 1 и 49.")

    if ticket_count == 1:
        warnings.append("Има само една валидна комбинация. Покритието на фиш се оценява по-добре при няколко комбинации.")
        recommendations.append("Добави още комбинации, за да се оцени реално разнообразието на фиша.")

    if duplicate_tickets:
        warnings.append("Открити са напълно еднакви комбинации.")
        recommendations.append("Замени дублираните комбинации с различни числа, за да увеличиш покритието.")

    if maximum_overlap >= 4:
        warnings.append("Някои комбинации споделят 4 или повече еднакви числа.")
        recommendations.append("Намали припокриването между комбинациите, за да покриеш повече различни сценарии.")

    if len(repeated_triples) > 0:
        warnings.append("Има повтарящи се тройки между различни комбинации.")
        recommendations.append("Повтарящите се тройки концентрират фиша. Разпредели числата по-разнообразно.")

    if len(repeated_pairs) > max(3, ticket_count * 2):
        warnings.append("Има много повтарящи се двойки.")
        recommendations.append("Намали повторението на двойки, ако целта е по-широко покритие.")

    if coverage_efficiency < 0.60 and ticket_count > 1:
        warnings.append("Уникалното покритие е ниско спрямо броя комбинации.")
        recommendations.append("Използвай повече различни числа между комбинациите.")

    if not warnings and ticket_count > 1:
        warnings.append("Не са открити сериозни проблеми в покритието.")

    if not recommendations and ticket_count > 1:
        recommendations.append("Фишът има приемливо разнообразие. Можеш да го сравниш и с оценката на фиш и анализа на двойки/групи.")

    return {
        "ticket_count": ticket_count,
        "invalid_count": invalid_count,
        "total_number_slots": total_slots,
        "unique_numbers": unique_numbers,
        "unique_numbers_count": unique_count,
        "unique_coverage_out_of_49": round(unique_coverage_49, 4),
        "max_possible_unique_numbers": max_possible_unique,
        "coverage_efficiency": round(coverage_efficiency, 4),
        "average_pairwise_overlap": round(average_overlap, 3),
        "maximum_pairwise_overlap": maximum_overlap,
        "repeated_pairs_count": len(repeated_pairs),
        "repeated_triples_count": len(repeated_triples),
        "duplicate_tickets_count": duplicate_tickets,
        "odd_even_distribution": {
            "odd": odd_count,
            "even": even_count,
        },
        "low_high_distribution": {
            "low_1_24": low_count,
            "high_25_49": high_count,
        },
        "range_distribution": {
            "1-9": range_distribution.get("1-9", 0),
            "10-19": range_distribution.get("10-19", 0),
            "20-29": range_distribution.get("20-29", 0),
            "30-39": range_distribution.get("30-39", 0),
            "40-49": range_distribution.get("40-49", 0),
        },
        "coverage_score": score,
        "band": _score_band(score),
        "warnings": warnings,
        "recommendations": recommendations,
        "validation_rows": validation_rows,
        "top_repeated_pairs": [
            {"pair": list(pair), "count": count}
            for pair, count in sorted(repeated_pairs.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
        "top_repeated_triples": [
            {"triple": list(triple), "count": count}
            for triple, count in sorted(repeated_triples.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
    }
