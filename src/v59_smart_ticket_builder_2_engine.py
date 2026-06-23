from __future__ import annotations

import json
import random
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any

import pandas as pd

from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center
from src.v58_smart_ensemble_score_engine import (
    analyze_single_smart_ensemble,
    analyze_smart_ensemble_scores,
)


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_TICKET = 6


def _number_weights(
    profiles: list[dict[str, Any]],
    hot_cold_center: dict[str, Any],
    strategy: str,
) -> dict[int, float]:
    profiles_by_number = {int(item["number"]): item for item in profiles}
    hot_by_number = {
        int(item["number"]): item
        for item in hot_cold_center.get("classified_numbers", [])
    }

    weights: dict[int, float] = {}

    for number in range(MIN_NUMBER, MAX_NUMBER + 1):
        profile = profiles_by_number.get(number, {})
        hot = hot_by_number.get(number, {})

        profile_score = float(profile.get("profile_score", 50.0))
        recent_activity = float(hot.get("recent_activity_score", 50.0))
        overdue_score = float(hot.get("overdue_score", 50.0))
        stability_score = float(hot.get("stability_score", 50.0))
        historical_strength = float(hot.get("historical_strength_score", 50.0))
        categories = hot.get("categories", [])

        weight = 1.0
        weight += profile_score / 100.0
        weight += historical_strength / 180.0
        weight += stability_score / 220.0

        if strategy == "Балансиран":
            if "Стабилно" in categories:
                weight += 0.45
            if "Исторически силно" in categories:
                weight += 0.25
            if "Закъсняло" in categories:
                weight += 0.20
            if "Горещо напоследък" in categories:
                weight += 0.15
            if "Исторически слабо" in categories:
                weight -= 0.15

        elif strategy == "Скорошна активност":
            weight += recent_activity / 120.0
            if "Горещо напоследък" in categories:
                weight += 0.55
            if "Студено напоследък" in categories:
                weight -= 0.25

        elif strategy == "Закъснели числа":
            weight += overdue_score / 100.0
            if "Закъсняло" in categories:
                weight += 0.70
            if "Горещо напоследък" in categories:
                weight -= 0.15

        elif strategy == "Стабилност":
            weight += stability_score / 80.0
            if "Стабилно" in categories:
                weight += 0.75
            if "Студено напоследък" in categories:
                weight -= 0.15

        elif strategy == "Експериментален":
            weight += recent_activity / 180.0
            weight += overdue_score / 160.0
            if "Скорошно активно, но не силно исторически" in categories:
                weight += 0.65
            if "Силно исторически, но тихо напоследък" in categories:
                weight += 0.45

        weights[number] = max(0.10, round(weight, 4))

    return weights


def _weighted_sample_without_replacement(
    weights: dict[int, float],
    rng: random.Random,
    k: int = NUMBERS_PER_TICKET,
) -> list[int]:
    available = list(weights.keys())
    selected: list[int] = []

    for _ in range(k):
        total_weight = sum(max(0.01, weights[number]) for number in available)

        if total_weight <= 0:
            choice = rng.choice(available)
        else:
            target = rng.random() * total_weight
            running = 0.0
            choice = available[-1]

            for number in available:
                running += max(0.01, weights[number])
                if running >= target:
                    choice = number
                    break

        selected.append(choice)
        available.remove(choice)

    return sorted(selected)


def _basic_candidate_ok(combo: list[int]) -> bool:
    numbers = sorted(combo)
    total_sum = sum(numbers)

    if total_sum < 85 or total_sum > 220:
        return False

    odd_count = sum(1 for number in numbers if number % 2 == 1)
    low_count = sum(1 for number in numbers if number <= 24)

    if odd_count in {0, 6}:
        return False

    if low_count in {0, 6}:
        return False

    longest_run = 1
    current = 1

    for left, right in zip(numbers, numbers[1:]):
        if right == left + 1:
            current += 1
            longest_run = max(longest_run, current)
        else:
            current = 1

    if longest_run >= 5:
        return False

    return True


def generate_candidate_combinations(
    candidate_count: int,
    seed: int,
    profiles: list[dict[str, Any]],
    hot_cold_center: dict[str, Any],
    strategy: str = "Балансиран",
) -> list[list[int]]:
    rng = random.Random(int(seed))
    weights = _number_weights(profiles, hot_cold_center, strategy)

    candidates: set[tuple[int, ...]] = set()
    attempts = 0
    max_attempts = max(1000, int(candidate_count) * 40)

    while len(candidates) < int(candidate_count) and attempts < max_attempts:
        attempts += 1
        combo = _weighted_sample_without_replacement(weights, rng, NUMBERS_PER_TICKET)

        if not _basic_candidate_ok(combo):
            continue

        candidates.add(tuple(combo))

    # Safe fallback with pure random combinations if filters are too strict.
    while len(candidates) < int(candidate_count) and attempts < max_attempts * 2:
        attempts += 1
        combo = sorted(rng.sample(range(MIN_NUMBER, MAX_NUMBER + 1), NUMBERS_PER_TICKET))
        candidates.add(tuple(combo))

    return [list(combo) for combo in sorted(candidates)]


def _pair_overlap(left: list[int], right: list[int]) -> int:
    left_pairs = set(combinations(sorted(left), 2))
    right_pairs = set(combinations(sorted(right), 2))
    return len(left_pairs.intersection(right_pairs))


def _number_overlap(left: list[int], right: list[int]) -> int:
    return len(set(left).intersection(right))


def _portfolio_diversity_ok(
    candidate: list[int],
    selected: list[list[int]],
    number_usage: dict[int, int],
    max_number_reuse: int,
    max_shared_numbers: int,
) -> bool:
    for number in candidate:
        if number_usage.get(number, 0) >= max_number_reuse:
            return False

    for existing in selected:
        if _number_overlap(candidate, existing) > max_shared_numbers:
            return False

        if _pair_overlap(candidate, existing) >= 4:
            return False

    return True


def _candidate_row(score_result: dict[str, Any]) -> dict[str, Any]:
    components = score_result.get("components", {})

    return {
        "combination": score_result.get("combination", []),
        "combination_text": score_result.get("combination_text", ""),
        "final_score": float(score_result.get("final_score", 0.0)),
        "band": score_result.get("band", ""),
        "pattern_score": float(components.get("pattern_score", 0.0)),
        "coverage_score": float(components.get("coverage_score", 0.0)),
        "number_profile_score": float(components.get("number_profile_score", 0.0)),
        "hot_cold_balance_score": float(components.get("hot_cold_balance_score", 0.0)),
        "similarity_context_score": float(components.get("similarity_context_score", 0.0)),
        "warnings": score_result.get("warnings", []),
        "recommendations": score_result.get("recommendations", []),
    }


def build_smart_ticket_builder_2(
    ticket_count: int = 5,
    candidate_count: int = 120,
    seed: int = 59,
    strategy: str = "Балансиран",
    max_number_reuse: int = 2,
    max_shared_numbers: int = 2,
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

    candidates = generate_candidate_combinations(
        candidate_count=candidate_count,
        seed=seed,
        profiles=profiles,
        hot_cold_center=hot_cold_center,
        strategy=strategy,
    )

    scored_candidates: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates, start=1):
        score_result = analyze_single_smart_ensemble(
            combo=candidate,
            index=index,
            draw_events=draw_events,
            profiles_by_number=profiles_by_number,
            hot_cold_by_number=hot_cold_by_number,
            portfolio_coverage_score=75.0,
        )

        if not score_result.get("is_valid"):
            continue

        scored_candidates.append(_candidate_row(score_result))

    scored_candidates.sort(
        key=lambda item: (
            item["final_score"],
            item["pattern_score"],
            item["number_profile_score"],
            item["hot_cold_balance_score"],
        ),
        reverse=True,
    )

    selected: list[list[int]] = []
    selected_rows: list[dict[str, Any]] = []
    number_usage: dict[int, int] = {}

    for row in scored_candidates:
        candidate = list(row["combination"])

        if _portfolio_diversity_ok(
            candidate=candidate,
            selected=selected,
            number_usage=number_usage,
            max_number_reuse=max_number_reuse,
            max_shared_numbers=max_shared_numbers,
        ):
            selected.append(candidate)
            selected_rows.append(row)

            for number in candidate:
                number_usage[number] = number_usage.get(number, 0) + 1

        if len(selected) >= int(ticket_count):
            break

    # Fallback pass with relaxed overlap if not enough tickets were selected.
    if len(selected) < int(ticket_count):
        for row in scored_candidates:
            candidate = list(row["combination"])

            if candidate in selected:
                continue

            too_reused = any(number_usage.get(number, 0) >= max_number_reuse + 1 for number in candidate)
            if too_reused:
                continue

            selected.append(candidate)
            selected_rows.append(row)

            for number in candidate:
                number_usage[number] = number_usage.get(number, 0) + 1

            if len(selected) >= int(ticket_count):
                break

    final_ensemble = analyze_smart_ensemble_scores(
        combinations=selected,
        draw_events=draw_events,
        profiles=profiles,
        hot_cold_center=hot_cold_center,
    ) if selected else {
        "average_final_score": 0.0,
        "best_score": 0.0,
        "weakest_score": 0.0,
        "portfolio_coverage": {},
        "analyses": [],
        "band": "Няма генерирани комбинации",
        "safety_note_bg": "Няма достатъчно данни за оценка.",
    }

    final_rows_by_combo = {
        tuple(item.get("combination", [])): item
        for item in final_ensemble.get("analyses", [])
    }

    final_selected_rows: list[dict[str, Any]] = []

    for combo in selected:
        item = final_rows_by_combo.get(tuple(combo))
        if item:
            final_selected_rows.append(_candidate_row(item))

    warnings: list[str] = []
    recommendations: list[str] = []

    if len(selected) < int(ticket_count):
        warnings.append("Генераторът избра по-малко комбинации от заявения брой.")
        recommendations.append("Увеличи броя кандидати или разреши по-голямо повторение на числа.")

    if final_ensemble.get("average_final_score", 0.0) < 55:
        warnings.append("Средната обединена оценка на предложения фиш е ниска.")
        recommendations.append("Пробвай друг seed, по-голям кандидатски пул или различна стратегия.")

    coverage_score = float(final_ensemble.get("portfolio_coverage", {}).get("coverage_score", 0.0) or 0.0)

    if coverage_score < 60 and len(selected) > 1:
        warnings.append("Покритието на предложения фиш не е достатъчно силно.")
        recommendations.append("Намали повторението между комбинациите или увеличи броя кандидати.")

    if not warnings:
        warnings.append("Не са открити сериозни проблеми в предложения фиш.")

    if not recommendations:
        recommendations.append("Предложеният фиш е подходящ за допълнителна проверка в модулите за баланс, покритие и историческа близост.")

    recommendations.append("Това не е предсказание и не е гаранция за печалба. Използвай го като статистически помощник за изграждане на фиш.")

    return {
        "total_draws": len(draw_events),
        "strategy": strategy,
        "seed": int(seed),
        "requested_ticket_count": int(ticket_count),
        "candidate_count_requested": int(candidate_count),
        "candidate_count_generated": len(candidates),
        "candidate_count_scored": len(scored_candidates),
        "selected_count": len(selected),
        "selected_tickets": selected,
        "selected_rows": final_selected_rows,
        "top_candidates_preview": scored_candidates[:20],
        "final_ensemble": final_ensemble,
        "average_final_score": float(final_ensemble.get("average_final_score", 0.0)),
        "best_score": float(final_ensemble.get("best_score", 0.0)),
        "weakest_score": float(final_ensemble.get("weakest_score", 0.0)),
        "coverage_score": coverage_score,
        "warnings": warnings,
        "recommendations": recommendations,
        "safety_note_bg": (
            "Умен генератор на комбинации 2 генерира статистически балансирани предложения. "
            "Той не предсказва печеливши числа и не гарантира печалба."
        ),
    }


def builder_result_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    rows = []

    for index, row in enumerate(result.get("selected_rows", []), start=1):
        rows.append(
            {
                "ticket_index": index,
                "combination": row.get("combination_text", ""),
                "final_score": row.get("final_score", 0.0),
                "band": row.get("band", ""),
                "pattern_score": row.get("pattern_score", 0.0),
                "coverage_score": row.get("coverage_score", 0.0),
                "number_profile_score": row.get("number_profile_score", 0.0),
                "hot_cold_balance_score": row.get("hot_cold_balance_score", 0.0),
                "similarity_context_score": row.get("similarity_context_score", 0.0),
            }
        )

    return pd.DataFrame(rows)


def export_builder_result(
    result: dict[str, Any],
    output_csv_path: str | Path,
    output_json_path: str | Path,
) -> None:
    df = builder_result_to_dataframe(result)
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_json_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
