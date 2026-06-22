from __future__ import annotations

import re
from collections import Counter
from typing import Any

from src.v55_number_profile_engine import load_draw_events


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_DRAW = 6


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

    if len(combo) != NUMBERS_PER_DRAW:
        errors.append("Комбинацията трябва да съдържа точно 6 числа.")

    if any(number < MIN_NUMBER or number > MAX_NUMBER for number in combo):
        errors.append("Всички числа трябва да са между 1 и 49.")

    if len(set(combo)) != len(combo):
        errors.append("Комбинацията съдържа повтарящи се числа.")

    return errors


def _clean_combo(combo: list[int]) -> list[int]:
    return sorted(int(number) for number in combo)


def _score_band(max_match_count: int, exact_count: int, five_count: int, four_count: int) -> str:
    if exact_count > 0:
        return "Има точно историческо съвпадение"
    if max_match_count >= 5:
        return "Има много близки исторически тиражи"
    if max_match_count == 4:
        return "Има близки исторически тиражи"
    if max_match_count == 3:
        return "Има умерена историческа близост"
    return "Няма силна историческа близост"


def _historical_similarity_score(
    max_match_count: int,
    exact_count: int,
    five_count: int,
    four_count: int,
    three_count: int,
) -> float:
    if exact_count > 0:
        return 100.0

    score = (max_match_count / NUMBERS_PER_DRAW) * 70.0
    score += min(15.0, five_count * 4.0)
    score += min(10.0, four_count * 1.5)
    score += min(5.0, three_count * 0.10)

    return round(max(0.0, min(100.0, score)), 2)


def _warnings_and_recommendations(
    exact_count: int,
    five_count: int,
    four_count: int,
    max_match_count: int,
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    recommendations: list[str] = []

    if exact_count > 0:
        warnings.append("Тази комбинация вече има точно историческо съвпадение в данните.")
        recommendations.append("Точното минало съвпадение не означава, че комбинацията е по-вероятна или по-малко вероятна в бъдеще.")
    elif five_count > 0:
        warnings.append("Има исторически тиражи с 5 съвпадащи числа.")
        recommendations.append("Използвай близките тиражи като контекст за сравнение, не като прогноза.")
    elif four_count > 0:
        warnings.append("Има исторически тиражи с 4 съвпадащи числа.")
        recommendations.append("Провери дали комбинацията не е прекалено близка до вече срещани исторически модели.")
    elif max_match_count <= 2:
        warnings.append("Не са открити силно близки исторически тиражи.")
        recommendations.append("Комбинацията изглежда по-различна спрямо миналите тегления, но това не променя математическата вероятност.")

    recommendations.append("Сравни резултата и с модулите за покритие, баланс и профил на число.")

    return warnings, recommendations


def analyze_single_combination_similarity(
    combo: list[int],
    draw_events: list[dict[str, Any]],
    top_n: int = 20,
    index: int = 1,
) -> dict[str, Any]:
    errors = validate_combination(combo)

    if errors:
        return {
            "query_index": index,
            "query_numbers": combo,
            "query_text": ", ".join(str(number) for number in combo),
            "is_valid": False,
            "status": " ".join(errors),
            "total_draws": len(draw_events),
            "historical_similarity_score": 0.0,
            "band": "Невалидна комбинация",
            "match_distribution": {str(i): 0 for i in range(7)},
            "closest_draws": [],
            "warnings": errors,
            "recommendations": ["Поправи комбинацията и я анализирай отново."],
        }

    query_numbers = _clean_combo(combo)
    query_set = set(query_numbers)

    distribution: Counter[int] = Counter()
    closest_rows: list[dict[str, Any]] = []

    for event in draw_events:
        draw_numbers = sorted(set(int(number) for number in event.get("numbers", [])))
        draw_set = set(draw_numbers)

        matching_numbers = sorted(query_set.intersection(draw_set))
        missing_from_draw = sorted(query_set.difference(draw_set))
        extra_in_draw = sorted(draw_set.difference(query_set))
        match_count = len(matching_numbers)

        distribution[match_count] += 1

        closest_rows.append(
            {
                "event_index": int(event.get("event_index", 0)),
                "year": event.get("year", ""),
                "draw_no": event.get("draw_no", ""),
                "date": event.get("date", ""),
                "draw_numbers": draw_numbers,
                "draw_numbers_text": ", ".join(str(number) for number in draw_numbers),
                "match_count": match_count,
                "matching_numbers": matching_numbers,
                "matching_numbers_text": ", ".join(str(number) for number in matching_numbers),
                "different_query_numbers": missing_from_draw,
                "different_query_numbers_text": ", ".join(str(number) for number in missing_from_draw),
                "different_draw_numbers": extra_in_draw,
                "different_draw_numbers_text": ", ".join(str(number) for number in extra_in_draw),
            }
        )

    closest_rows = sorted(
        closest_rows,
        key=lambda row: (-int(row["match_count"]), -int(row["event_index"])),
    )

    limited_closest_rows = closest_rows[: max(1, int(top_n))]

    exact_count = distribution.get(6, 0)
    five_count = distribution.get(5, 0)
    four_count = distribution.get(4, 0)
    three_count = distribution.get(3, 0)
    max_match_count = int(limited_closest_rows[0]["match_count"]) if limited_closest_rows else 0

    score = _historical_similarity_score(
        max_match_count=max_match_count,
        exact_count=exact_count,
        five_count=five_count,
        four_count=four_count,
        three_count=three_count,
    )

    band = _score_band(max_match_count, exact_count, five_count, four_count)
    warnings, recommendations = _warnings_and_recommendations(
        exact_count=exact_count,
        five_count=five_count,
        four_count=four_count,
        max_match_count=max_match_count,
    )

    return {
        "query_index": index,
        "query_numbers": query_numbers,
        "query_text": ", ".join(str(number) for number in query_numbers),
        "is_valid": True,
        "status": "Валидна",
        "total_draws": len(draw_events),
        "historical_similarity_score": score,
        "band": band,
        "max_match_count": max_match_count,
        "exact_matches_count": exact_count,
        "five_matches_count": five_count,
        "four_matches_count": four_count,
        "three_matches_count": three_count,
        "match_distribution": {
            str(i): int(distribution.get(i, 0))
            for i in range(6, -1, -1)
        },
        "closest_draws": limited_closest_rows,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def analyze_draw_similarity(
    combinations: list[list[int]],
    draw_events: list[dict[str, Any]] | None = None,
    top_n: int = 20,
) -> dict[str, Any]:
    if draw_events is None:
        draw_events = load_draw_events()

    analyses = [
        analyze_single_combination_similarity(
            combo=combo,
            draw_events=draw_events,
            top_n=top_n,
            index=index,
        )
        for index, combo in enumerate(combinations, start=1)
    ]

    valid_analyses = [item for item in analyses if item.get("is_valid")]
    invalid_count = len(analyses) - len(valid_analyses)

    if valid_analyses:
        average_score = round(
            sum(float(item["historical_similarity_score"]) for item in valid_analyses) / len(valid_analyses),
            2,
        )
        best_max_match = max(int(item.get("max_match_count", 0)) for item in valid_analyses)
        total_exact = sum(int(item.get("exact_matches_count", 0)) for item in valid_analyses)
    else:
        average_score = 0.0
        best_max_match = 0
        total_exact = 0

    return {
        "total_draws": len(draw_events),
        "query_count": len(combinations),
        "valid_count": len(valid_analyses),
        "invalid_count": invalid_count,
        "average_historical_similarity_score": average_score,
        "best_max_match_count": best_max_match,
        "total_exact_matches": total_exact,
        "analyses": analyses,
        "safety_note_bg": (
            "Това е историческо сравнение, не предсказание. "
            "Сходството с минали тиражи не променя математическата вероятност за бъдещ тираж."
        ),
    }
