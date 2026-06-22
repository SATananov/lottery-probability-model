from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.v55_number_profile_engine import build_number_profiles, load_draw_events


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_DRAW = 6


def _expected_recent(window: int) -> float:
    return window * NUMBERS_PER_DRAW / MAX_NUMBER


def _safe_ratio(value: float, expected: float) -> float:
    if expected <= 0:
        return 0.0
    return round(value / expected, 4)


def _classify_number(profile: dict[str, Any]) -> dict[str, Any]:
    number = int(profile["number"])

    appearances = int(profile["appearances"])
    expected_appearances = float(profile["expected_appearances"])
    expected_ratio = float(profile["appearance_vs_expected_ratio"])

    recent_50 = int(profile["recent_50"])
    recent_100 = int(profile["recent_100"])
    recent_250 = int(profile["recent_250"])

    expected_50 = _expected_recent(50)
    expected_100 = _expected_recent(100)
    expected_250 = _expected_recent(250)

    recent_50_ratio = _safe_ratio(recent_50, expected_50)
    recent_100_ratio = _safe_ratio(recent_100, expected_100)
    recent_250_ratio = _safe_ratio(recent_250, expected_250)

    draws_since_last = int(profile["draws_since_last_seen"])
    average_interval = float(profile["average_interval"] or 0.0)
    gap_ratio = float(profile["current_gap_ratio"] or 0.0)
    stability = float(profile["interval_stability_score"] or 0.0)
    profile_score = float(profile["profile_score"] or 0.0)

    historical_strength_score = max(0.0, min(100.0, round(expected_ratio * 50.0, 2)))
    recent_activity_score = max(
        0.0,
        min(
            100.0,
            round(
                recent_50_ratio * 45.0
                + recent_100_ratio * 30.0
                + recent_250_ratio * 25.0,
                2,
            ),
        ),
    )

    overdue_score = max(
        0.0,
        min(
            100.0,
            round(gap_ratio * 42.0 if average_interval > 0 else draws_since_last * 2.0, 2),
        ),
    )

    stability_score = max(0.0, min(100.0, round(stability, 2)))

    categories: list[str] = []

    if recent_50_ratio >= 1.45 or recent_100_ratio >= 1.35:
        categories.append("Горещо напоследък")

    if recent_100_ratio <= 0.65 and recent_250_ratio <= 0.80:
        categories.append("Студено напоследък")

    if gap_ratio >= 1.5 or draws_since_last >= max(14, average_interval * 1.5 if average_interval else 18):
        categories.append("Закъсняло")

    if expected_ratio >= 1.05:
        categories.append("Исторически силно")

    if expected_ratio <= 0.95:
        categories.append("Исторически слабо")

    if stability_score >= 65 and 0.85 <= recent_250_ratio <= 1.20:
        categories.append("Стабилно")

    if expected_ratio >= 1.03 and recent_100_ratio <= 0.75:
        categories.append("Силно исторически, но тихо напоследък")

    if expected_ratio <= 0.98 and recent_50_ratio >= 1.35:
        categories.append("Скорошно активно, но не силно исторически")

    if not categories:
        categories.append("Неутрален профил")

    combined_score = round(
        historical_strength_score * 0.25
        + recent_activity_score * 0.30
        + overdue_score * 0.20
        + stability_score * 0.15
        + profile_score * 0.10,
        2,
    )

    if "Горещо напоследък" in categories:
        main_group = "Горещи напоследък"
    elif "Закъсняло" in categories:
        main_group = "Закъснели"
    elif "Студено напоследък" in categories:
        main_group = "Студени напоследък"
    elif "Стабилно" in categories:
        main_group = "Стабилни"
    elif "Исторически силно" in categories:
        main_group = "Исторически силни"
    elif "Исторически слабо" in categories:
        main_group = "Исторически слаби"
    else:
        main_group = "Неутрални"

    explanation = [
        f"Число {number} има {appearances} исторически появи при очаквани около {expected_appearances}.",
        f"В последните 50 тиража има {recent_50} появи, а в последните 100 тиража има {recent_100} появи.",
        f"От последната поява са минали {draws_since_last} тиража.",
    ]

    recommendations = [
        "Използвай групата като статистически контекст, не като прогноза.",
        "Сравни числото с профила му, баланса на комбинацията и покритието на фиша.",
    ]

    return {
        "number": number,
        "main_group": main_group,
        "categories": categories,
        "categories_text": ", ".join(categories),
        "combined_score": combined_score,
        "historical_strength_score": historical_strength_score,
        "recent_activity_score": recent_activity_score,
        "overdue_score": overdue_score,
        "stability_score": stability_score,
        "profile_score": profile_score,
        "appearances": appearances,
        "expected_appearances": expected_appearances,
        "appearance_vs_expected_ratio": expected_ratio,
        "recent_50": recent_50,
        "recent_100": recent_100,
        "recent_250": recent_250,
        "recent_50_ratio": recent_50_ratio,
        "recent_100_ratio": recent_100_ratio,
        "recent_250_ratio": recent_250_ratio,
        "draws_since_last_seen": draws_since_last,
        "average_interval": average_interval,
        "current_gap_ratio": gap_ratio,
        "interval_stability_score": stability_score,
        "source_status": profile.get("status", ""),
        "source_band": profile.get("band", ""),
        "explanation": explanation,
        "recommendations": recommendations,
    }


def build_hot_cold_stable_center(
    draw_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if draw_events is None:
        draw_events = load_draw_events()

    profiles = build_number_profiles(draw_events)
    classified = [_classify_number(profile) for profile in profiles]

    groups: dict[str, list[dict[str, Any]]] = {}

    group_order = [
        "Горещи напоследък",
        "Студени напоследък",
        "Закъснели",
        "Стабилни",
        "Исторически силни",
        "Исторически слаби",
        "Неутрални",
    ]

    for group in group_order:
        groups[group] = []

    for item in classified:
        groups.setdefault(item["main_group"], []).append(item)

    for group, rows in groups.items():
        if group in {"Студени напоследък", "Закъснели"}:
            rows.sort(key=lambda item: (item["overdue_score"], item["draws_since_last_seen"]), reverse=True)
        else:
            rows.sort(key=lambda item: item["combined_score"], reverse=True)

    summary_rows = []
    for group in group_order:
        summary_rows.append(
            {
                "group": group,
                "count": len(groups.get(group, [])),
                "numbers": [item["number"] for item in groups.get(group, [])],
            }
        )

    top_hot = sorted(classified, key=lambda item: item["recent_activity_score"], reverse=True)[:10]
    top_cold = sorted(classified, key=lambda item: (item["recent_100_ratio"], item["recent_250_ratio"]))[:10]
    top_overdue = sorted(classified, key=lambda item: item["draws_since_last_seen"], reverse=True)[:10]
    top_stable = sorted(classified, key=lambda item: item["stability_score"], reverse=True)[:10]
    top_historical = sorted(classified, key=lambda item: item["historical_strength_score"], reverse=True)[:10]

    return {
        "total_draws": len(draw_events),
        "numbers_profiled": len(classified),
        "data_path": str(draw_events[0].get("data_path", "")) if draw_events else "",
        "classified_numbers": classified,
        "groups": groups,
        "summary_rows": summary_rows,
        "top_hot": top_hot,
        "top_cold": top_cold,
        "top_overdue": top_overdue,
        "top_stable": top_stable,
        "top_historical": top_historical,
        "safety_note_bg": (
            "Това е историческа статистическа класификация, не предсказание. "
            "Групите показват минало поведение и текущ ритъм, но не гарантират бъдещо теглене."
        ),
    }


def center_to_dataframe(center: dict[str, Any]) -> pd.DataFrame:
    rows = []

    for item in center["classified_numbers"]:
        rows.append(
            {
                "number": item["number"],
                "main_group": item["main_group"],
                "categories": item["categories_text"],
                "combined_score": item["combined_score"],
                "historical_strength_score": item["historical_strength_score"],
                "recent_activity_score": item["recent_activity_score"],
                "overdue_score": item["overdue_score"],
                "stability_score": item["stability_score"],
                "profile_score": item["profile_score"],
                "appearances": item["appearances"],
                "appearance_vs_expected_ratio": item["appearance_vs_expected_ratio"],
                "recent_50": item["recent_50"],
                "recent_100": item["recent_100"],
                "recent_250": item["recent_250"],
                "recent_50_ratio": item["recent_50_ratio"],
                "recent_100_ratio": item["recent_100_ratio"],
                "recent_250_ratio": item["recent_250_ratio"],
                "draws_since_last_seen": item["draws_since_last_seen"],
                "average_interval": item["average_interval"],
                "current_gap_ratio": item["current_gap_ratio"],
                "interval_stability_score": item["interval_stability_score"],
            }
        )

    return pd.DataFrame(rows)


def export_hot_cold_stable_center(
    center: dict[str, Any],
    output_csv_path: str | Path,
    output_json_path: str | Path,
) -> None:
    df = center_to_dataframe(center)
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    safe_center = {
        "total_draws": center["total_draws"],
        "numbers_profiled": center["numbers_profiled"],
        "data_path": center["data_path"],
        "summary_rows": center["summary_rows"],
        "classified_numbers": center["classified_numbers"],
        "safety_note_bg": center["safety_note_bg"],
    }

    Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_json_path).write_text(
        json.dumps(safe_center, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
