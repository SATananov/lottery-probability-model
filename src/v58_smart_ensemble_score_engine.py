from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

import pandas as pd

from src.v53_ticket_coverage_engine import analyze_ticket_coverage
from src.v54_pattern_balance_engine import analyze_combination_pattern
from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v56_draw_similarity_engine import analyze_single_combination_similarity
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_COMBINATION = 6


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

    if len(combo) != NUMBERS_PER_COMBINATION:
        errors.append("Комбинацията трябва да съдържа точно 6 числа.")

    if any(number < MIN_NUMBER or number > MAX_NUMBER for number in combo):
        errors.append("Всички числа трябва да са между 1 и 49.")

    if len(set(combo)) != len(combo):
        errors.append("Комбинацията съдържа повтарящи се числа.")

    return errors


def _score_band(score: float) -> str:
    if score >= 82:
        return "Много силна статистическа структура"
    if score >= 68:
        return "Добра статистическа структура"
    if score >= 52:
        return "Средна статистическа структура"
    return "Слаба или прекалено крайна структура"


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 2)


def _similarity_context_score(similarity: dict[str, Any]) -> float:
    if not similarity.get("is_valid"):
        return 0.0

    exact = int(similarity.get("exact_matches_count", 0))
    five = int(similarity.get("five_matches_count", 0))
    four = int(similarity.get("four_matches_count", 0))
    max_match = int(similarity.get("max_match_count", 0))

    if exact > 0:
        return 60.0
    if five > 0:
        return 66.0
    if four > 0:
        return 80.0
    if max_match == 3:
        return 84.0
    if max_match <= 2:
        return 76.0

    return 72.0


def _hot_cold_balance_score(items: list[dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    if not items:
        return 0.0, {
            "hot_count": 0,
            "cold_count": 0,
            "stable_count": 0,
            "overdue_count": 0,
            "historically_strong_count": 0,
            "historically_weak_count": 0,
            "average_recent_activity": 0.0,
            "average_stability": 0.0,
            "average_overdue": 0.0,
        }

    hot_count = 0
    cold_count = 0
    stable_count = 0
    overdue_count = 0
    historically_strong_count = 0
    historically_weak_count = 0

    recent_scores = []
    stability_scores = []
    overdue_scores = []

    for item in items:
        categories = item.get("categories", [])

        if "Горещо напоследък" in categories:
            hot_count += 1
        if "Студено напоследък" in categories:
            cold_count += 1
        if "Стабилно" in categories:
            stable_count += 1
        if "Закъсняло" in categories:
            overdue_count += 1
        if "Исторически силно" in categories:
            historically_strong_count += 1
        if "Исторически слабо" in categories:
            historically_weak_count += 1

        recent_scores.append(float(item.get("recent_activity_score", 0.0)))
        stability_scores.append(float(item.get("stability_score", 0.0)))
        overdue_scores.append(float(item.get("overdue_score", 0.0)))

    score = 74.0

    if 1 <= hot_count <= 3:
        score += 6.0
    elif hot_count >= 5:
        score -= 8.0

    if 1 <= overdue_count <= 3:
        score += 5.0
    elif overdue_count >= 5:
        score -= 8.0

    if stable_count >= 2:
        score += 6.0

    if historically_strong_count >= 2:
        score += 4.0

    if historically_weak_count >= 4:
        score -= 6.0

    if cold_count >= 5:
        score -= 8.0

    details = {
        "hot_count": hot_count,
        "cold_count": cold_count,
        "stable_count": stable_count,
        "overdue_count": overdue_count,
        "historically_strong_count": historically_strong_count,
        "historically_weak_count": historically_weak_count,
        "average_recent_activity": round(mean(recent_scores), 2) if recent_scores else 0.0,
        "average_stability": round(mean(stability_scores), 2) if stability_scores else 0.0,
        "average_overdue": round(mean(overdue_scores), 2) if overdue_scores else 0.0,
    }

    return _clamp_score(score), details


def _number_profile_score(combo: list[int], profiles_by_number: dict[int, dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    scores = []
    statuses = []
    bands = []

    for number in combo:
        profile = profiles_by_number.get(int(number))
        if not profile:
            continue

        scores.append(float(profile.get("profile_score", 0.0)))
        statuses.append(str(profile.get("status", "")))
        bands.append(str(profile.get("band", "")))

    if not scores:
        return 0.0, {
            "average_profile_score": 0.0,
            "min_profile_score": 0.0,
            "max_profile_score": 0.0,
            "statuses": [],
            "bands": [],
        }

    details = {
        "average_profile_score": round(mean(scores), 2),
        "min_profile_score": round(min(scores), 2),
        "max_profile_score": round(max(scores), 2),
        "statuses": statuses,
        "bands": bands,
    }

    return _clamp_score(details["average_profile_score"]), details


def _warnings_and_recommendations(
    final_score: float,
    pattern_score: float,
    coverage_score: float,
    similarity: dict[str, Any],
    hot_cold_details: dict[str, Any],
    number_profile_details: dict[str, Any],
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    recommendations: list[str] = []

    if final_score < 52:
        warnings.append("Обединената оценка е ниска. Има няколко структурни или статистически слабости.")
        recommendations.append("Прегледай отделните компоненти: баланс, профил на числа, историческа близост и покритие.")

    if pattern_score < 55:
        warnings.append("Структурният баланс на комбинацията е слаб или прекалено краен.")
        recommendations.append("Провери четни/нечетни, ниски/високи, сума, поредици и разстояния.")

    if coverage_score < 55:
        warnings.append("Покритието на фиша е концентрирано или комбинациите се припокриват твърде много.")
        recommendations.append("Намали повторенията между комбинациите и увеличи уникалните числа във фиша.")

    if int(similarity.get("exact_matches_count", 0)) > 0:
        warnings.append("Комбинацията има точно историческо съвпадение.")
        recommendations.append("Точното минало съвпадение е само исторически факт, не сигнал за бъдещо теглене.")

    if int(similarity.get("five_matches_count", 0)) > 0:
        warnings.append("Комбинацията има много близки исторически тиражи с 5 съвпадения.")
        recommendations.append("Използвай това само като контекст за сходство с минали тегления.")

    if hot_cold_details.get("cold_count", 0) >= 5:
        warnings.append("Комбинацията съдържа много числа, които са студени напоследък.")
        recommendations.append("Помисли дали да не смесиш студени, стабилни и активни числа по-балансирано.")

    if hot_cold_details.get("hot_count", 0) >= 5:
        warnings.append("Комбинацията е силно натоварена с горещи напоследък числа.")
        recommendations.append("Избягвай прекалено едностранен избор само по скорошна активност.")

    if number_profile_details.get("average_profile_score", 0) < 45:
        warnings.append("Средният профил на избраните числа е слаб.")
        recommendations.append("Сравни числата в страницата „Профил на число“ и замени най-слабите кандидати.")

    if not warnings:
        warnings.append("Не са открити сериозни проблеми в обединената оценка.")

    if not recommendations:
        recommendations.append("Комбинацията изглежда балансирана като статистическа структура. Провери я и в отделните модули.")

    recommendations.append("Това не е предсказание и не е гаранция за печалба. Използвай резултата само като помощ за статистически контрол.")

    return warnings, recommendations


def analyze_single_smart_ensemble(
    combo: list[int],
    index: int,
    draw_events: list[dict[str, Any]],
    profiles_by_number: dict[int, dict[str, Any]],
    hot_cold_by_number: dict[int, dict[str, Any]],
    portfolio_coverage_score: float,
) -> dict[str, Any]:
    errors = validate_combination(combo)

    if errors:
        return {
            "query_index": index,
            "combination": combo,
            "combination_text": ", ".join(str(number) for number in combo),
            "is_valid": False,
            "status": " ".join(errors),
            "final_score": 0.0,
            "band": "Невалидна комбинация",
            "warnings": errors,
            "recommendations": ["Поправи комбинацията и я анализирай отново."],
        }

    numbers = sorted(int(number) for number in combo)

    pattern = analyze_combination_pattern(numbers, index=index)
    pattern_score = float(pattern.get("pattern_score", 0.0))

    similarity = analyze_single_combination_similarity(
        combo=numbers,
        draw_events=draw_events,
        top_n=10,
        index=index,
    )
    similarity_score = _similarity_context_score(similarity)

    number_profile_score, number_profile_details = _number_profile_score(numbers, profiles_by_number)

    hot_cold_items = [
        hot_cold_by_number[number]
        for number in numbers
        if number in hot_cold_by_number
    ]
    hot_cold_score, hot_cold_details = _hot_cold_balance_score(hot_cold_items)

    coverage_score = float(portfolio_coverage_score)

    final_score = _clamp_score(
        pattern_score * 0.22
        + coverage_score * 0.16
        + number_profile_score * 0.24
        + hot_cold_score * 0.20
        + similarity_score * 0.18
    )

    warnings, recommendations = _warnings_and_recommendations(
        final_score=final_score,
        pattern_score=pattern_score,
        coverage_score=coverage_score,
        similarity=similarity,
        hot_cold_details=hot_cold_details,
        number_profile_details=number_profile_details,
    )

    components = {
        "pattern_score": round(pattern_score, 2),
        "coverage_score": round(coverage_score, 2),
        "number_profile_score": round(number_profile_score, 2),
        "hot_cold_balance_score": round(hot_cold_score, 2),
        "similarity_context_score": round(similarity_score, 2),
    }

    return {
        "query_index": index,
        "combination": numbers,
        "combination_text": ", ".join(str(number) for number in numbers),
        "is_valid": True,
        "status": "Валидна",
        "final_score": final_score,
        "band": _score_band(final_score),
        "components": components,
        "pattern": pattern,
        "similarity": similarity,
        "number_profile_details": number_profile_details,
        "hot_cold_details": hot_cold_details,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def analyze_smart_ensemble_scores(
    combinations: list[list[int]],
    draw_events: list[dict[str, Any]] | None = None,
    profiles: list[dict[str, Any]] | None = None,
    hot_cold_center: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if draw_events is None:
        draw_events = load_draw_events()

    if profiles is None:
        profiles = build_number_profiles(draw_events)

    if hot_cold_center is None:
        hot_cold_center = build_hot_cold_stable_center(draw_events)

    profiles_by_number = {
        int(profile["number"]): profile
        for profile in profiles
    }

    hot_cold_by_number = {
        int(item["number"]): item
        for item in hot_cold_center.get("classified_numbers", [])
    }

    coverage = analyze_ticket_coverage(combinations)
    portfolio_coverage_score = float(coverage.get("coverage_score", 0.0))

    analyses = [
        analyze_single_smart_ensemble(
            combo=combo,
            index=index,
            draw_events=draw_events,
            profiles_by_number=profiles_by_number,
            hot_cold_by_number=hot_cold_by_number,
            portfolio_coverage_score=portfolio_coverage_score,
        )
        for index, combo in enumerate(combinations, start=1)
    ]

    valid_analyses = [item for item in analyses if item.get("is_valid")]
    invalid_count = len(analyses) - len(valid_analyses)

    if valid_analyses:
        average_final_score = round(mean(float(item["final_score"]) for item in valid_analyses), 2)
        best_score = max(float(item["final_score"]) for item in valid_analyses)
        weakest_score = min(float(item["final_score"]) for item in valid_analyses)
    else:
        average_final_score = 0.0
        best_score = 0.0
        weakest_score = 0.0

    return {
        "total_draws": len(draw_events),
        "query_count": len(combinations),
        "valid_count": len(valid_analyses),
        "invalid_count": invalid_count,
        "average_final_score": average_final_score,
        "best_score": round(best_score, 2),
        "weakest_score": round(weakest_score, 2),
        "portfolio_coverage": coverage,
        "analyses": analyses,
        "band": _score_band(average_final_score),
        "safety_note_bg": (
            "Обединената оценка е статистически контролен слой. "
            "Тя не предсказва печеливши числа и не увеличава математическата гаранция за печалба."
        ),
    }


def ensemble_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    rows = []

    for item in result.get("analyses", []):
        components = item.get("components", {})

        rows.append(
            {
                "query_index": item.get("query_index"),
                "combination": item.get("combination_text"),
                "is_valid": item.get("is_valid"),
                "status": item.get("status"),
                "final_score": item.get("final_score"),
                "band": item.get("band"),
                "pattern_score": components.get("pattern_score", 0.0),
                "coverage_score": components.get("coverage_score", 0.0),
                "number_profile_score": components.get("number_profile_score", 0.0),
                "hot_cold_balance_score": components.get("hot_cold_balance_score", 0.0),
                "similarity_context_score": components.get("similarity_context_score", 0.0),
            }
        )

    return pd.DataFrame(rows)


def export_smart_ensemble_result(
    result: dict[str, Any],
    output_csv_path: str | Path,
    output_json_path: str | Path,
) -> None:
    df = ensemble_to_dataframe(result)
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_json_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
