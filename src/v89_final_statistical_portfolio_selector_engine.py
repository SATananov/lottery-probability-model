
from __future__ import annotations

import csv
import itertools
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

TOTAL_NUMBERS = 49
DRAW_SIZE = 6

MODEL_PATH = ROOT / "models" / "v89" / "v89_final_statistical_portfolio_selector_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v89_final_statistical_portfolio_selector_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v89_final_statistical_portfolio_selector_summary.md"
ANALYSIS_CSV_PATH = ROOT / "reports" / "v89_final_statistical_portfolio_selector_analysis.csv"


def _t(value: str) -> str:
    return value.encode("utf-8").decode("unicode_escape")


MODE_LABELS = {
    "balanced": _t("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d"),
    "conservative": _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u0435\\u043d"),
    "aggressive": _t("\\u0410\\u0433\\u0440\\u0435\\u0441\\u0438\\u0432\\u0435\\u043d"),
}

MODE_DESCRIPTIONS = {
    "balanced": _t("\\u041d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u044a\\u0440 \\u043a\\u043e\\u043c\\u043f\\u0440\\u043e\\u043c\\u0438\\u0441 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u0441\\u0438\\u043b\\u0430 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435, \\u043a\\u0430\\u0447\\u0435\\u0441\\u0442\\u0432\\u043e \\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435 \\u0438 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435."),
    "conservative": _t("\\u0414\\u0430\\u0432\\u0430 \\u043f\\u043e-\\u0433\\u043e\\u043b\\u044f\\u043c\\u0430 \\u0442\\u0435\\u0436\\u0435\\u0441\\u0442 \\u043d\\u0430 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435\\u0442\\u043e \\u0438 \\u043f\\u043e-\\u043d\\u0438\\u0441\\u044a\\u043a \\u0440\\u0438\\u0441\\u043a \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442."),
    "aggressive": _t("\\u0414\\u0430\\u0432\\u0430 \\u043f\\u043e-\\u0433\\u043e\\u043b\\u044f\\u043c\\u0430 \\u0442\\u0435\\u0436\\u0435\\u0441\\u0442 \\u043d\\u0430 \\u043d\\u0430\\u0439-\\u0441\\u0438\\u043b\\u043d\\u0438\\u0442\\u0435 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430, \\u043d\\u043e \\u043f\\u0430\\u0437\\u0438 \\u043c\\u0438\\u043d\\u0438\\u043c\\u0430\\u043b\\u0435\\u043d \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b \\u043d\\u0430 \\u0440\\u0438\\u0441\\u043a\\u0430."),
}

MODE_WEIGHTS = {
    "balanced": {"model": 0.50, "quality": 0.20, "anti_zero": 0.20, "safety": 0.10},
    "conservative": {"model": 0.35, "quality": 0.20, "anti_zero": 0.35, "safety": 0.10},
    "aggressive": {"model": 0.70, "quality": 0.15, "anti_zero": 0.05, "safety": 0.10},
}

PACKAGE_SOURCES = [
    {
        "id": "final_play_plan",
        "label": _t("\\u0424\\u0438\\u043d\\u0430\\u043b\\u0435\\u043d \\u043f\\u043b\\u0430\\u043d \\u0437\\u0430 \\u0438\\u0433\\u0440\\u0430"),
        "paths": [
            "models/v78/v78_final_play_plan_model.json",
            "reports/v78_final_play_plan_summary.json",
            "reports/v78_final_play_plan_tickets.csv",
        ],
    },
    {
        "id": "applied_improved",
        "label": _t("\\u041f\\u0440\\u0438\\u043b\\u043e\\u0436\\u0435\\u043d \\u043f\\u043e\\u0434\\u043e\\u0431\\u0440\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442"),
        "paths": [
            "models/v70/v70_applied_portfolio_model.json",
            "reports/v70_applied_portfolio_summary.json",
            "reports/v70_applied_portfolio_tickets.csv",
        ],
    },
    {
        "id": "ticket_pack",
        "label": _t("\\u041f\\u0430\\u043a\\u0435\\u0442 \\u0437\\u0430 \\u0438\\u0433\\u0440\\u0430"),
        "paths": [
            "models/v71/v71_ticket_pack_model.json",
            "reports/v71_ticket_pack_summary.json",
            "reports/v71_ticket_pack_export.csv",
            "reports/v71_ticket_pack.csv",
        ],
    },
    {
        "id": "anti_zero_reference",
        "label": _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u0435\\u043d \\u0432\\u0430\\u0440\\u0438\\u0430\\u043d\\u0442 \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u0444\\u0438\\u0448"),
        "paths": [
            "models/v88/v88_anti_zero_coverage_model.json",
            "reports/v88_anti_zero_coverage_summary.json",
            "reports/v88_anti_zero_coverage_analysis.csv",
        ],
    },
    {
        "id": "weighted_generator",
        "label": _t("\\u0423\\u043c\\u0435\\u043d \\u0433\\u0435\\u043d\\u0435\\u0440\\u0430\\u0442\\u043e\\u0440 \\u0441 \\u0442\\u0435\\u0433\\u043b\\u0430"),
        "paths": [
            "models/v67/v67_weighted_ticket_builder_model.json",
            "reports/v67_weighted_ticket_builder_summary.json",
            "reports/v67_weighted_ticket_builder_tickets.csv",
        ],
    },
]

NUMBER_SCORE_PATHS = [
    "reports/v66_weighted_number_scores.csv",
    "models/v66/v66_weighted_number_scores_model.json",
    "models/v66/v66_weighted_number_scores.json",
    "reports/v58_smart_ensemble_scores_sample.csv",
    "reports/v41_current_pro_ticket_score.csv",
]

HISTORICAL_PATHS = [
    "data/v41_canonical_draw_events.csv",
    "data/v40_normalized_draw_events.csv",
    "data/historical_draws.csv",
]


def safe_comb(n: int, k: int) -> int:
    if n < 0 or k < 0 or k > n:
        return 0
    try:
        return math.comb(n, k)
    except ValueError:
        return 0


def calculate_empty_risk(unique_covered_numbers: int) -> dict[str, float]:
    unique = max(0, min(TOTAL_NUMBERS, int(unique_covered_numbers)))
    denominator = safe_comb(TOTAL_NUMBERS, DRAW_SIZE)
    numerator = safe_comb(TOTAL_NUMBERS - unique, DRAW_SIZE)
    empty = numerator / denominator if denominator else 0.0
    hit = 1.0 - empty
    return {
        "unique_covered_numbers": unique,
        "empty_risk_percent": empty * 100.0,
        "at_least_one_hit_percent": hit * 100.0,
    }


def _parse_int(value: Any) -> int | None:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    if 1 <= number <= TOTAL_NUMBERS:
        return number
    return None


def normalize_combination(value: Any) -> list[int]:
    if isinstance(value, str):
        raw_values = re.findall(r"\\d+", value)
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        return []

    numbers: list[int] = []
    seen: set[int] = set()
    for item in raw_values:
        number = _parse_int(item)
        if number is not None and number not in seen:
            seen.add(number)
            numbers.append(number)

    numbers = sorted(numbers)
    return numbers if len(numbers) == DRAW_SIZE else []


def _dedupe_combinations(combinations: list[list[int]]) -> list[list[int]]:
    result: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for combo in combinations:
        normalized = normalize_combination(combo)
        key = tuple(normalized)
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


NUMBER_FIELD_GROUPS = [
    ("n1", "n2", "n3", "n4", "n5", "n6"),
    ("number_1", "number_2", "number_3", "number_4", "number_5", "number_6"),
    ("main_1", "main_2", "main_3", "main_4", "main_5", "main_6"),
]


def extract_combinations_from_payload(payload: Any) -> list[list[int]]:
    results: list[list[int]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for keys in NUMBER_FIELD_GROUPS:
                if all(key in value for key in keys):
                    combo = normalize_combination([value.get(key) for key in keys])
                    if combo:
                        results.append(combo)

            for key in (
                "numbers",
                "combination",
                "selected_numbers",
                "main_numbers",
                "ticket_numbers",
                "field_numbers",
                "candidate_combinations",
                "current_combinations",
                "final_combinations",
                "active_combinations",
            ):
                if key in value:
                    combo = normalize_combination(value.get(key))
                    if combo:
                        results.append(combo)
                    else:
                        walk(value.get(key))

            for nested in value.values():
                if isinstance(nested, (dict, list, tuple)):
                    walk(nested)

        elif isinstance(value, (list, tuple)):
            combo = normalize_combination(value)
            if combo:
                results.append(combo)
            for item in value:
                if isinstance(item, (dict, list, tuple)):
                    walk(item)

    walk(payload)
    return _dedupe_combinations(results)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _load_csv_combinations(path: Path) -> list[list[int]]:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return []

    combinations: list[list[int]] = []

    for row in rows:
        for keys in NUMBER_FIELD_GROUPS:
            if all(key in row and str(row.get(key, "")).strip() for key in keys):
                combo = normalize_combination([row.get(key) for key in keys])
                if combo:
                    combinations.append(combo)

        for key in ("numbers", "combination", "selected_numbers", "main_numbers", "ticket_numbers"):
            if key in row and str(row.get(key, "")).strip():
                combo = normalize_combination(row.get(key))
                if combo:
                    combinations.append(combo)

    return _dedupe_combinations(combinations)


def _load_combinations_from_path(path: Path) -> list[list[int]]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".csv":
        return _load_csv_combinations(path)
    payload = _load_json(path)
    return extract_combinations_from_payload(payload)


def load_candidate_packages() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_signatures: set[tuple[tuple[int, ...], ...]] = set()

    for source in PACKAGE_SOURCES:
        all_combinations: list[list[int]] = []
        used_path = None
        for rel_path in source["paths"]:
            path = ROOT / rel_path
            combos = _load_combinations_from_path(path)
            if combos:
                all_combinations = combos
                used_path = rel_path
                break

        clean = _dedupe_combinations(all_combinations)
        if not clean:
            continue

        if len(clean) > 8:
            clean = clean[:8]

        signature = tuple(tuple(combo) for combo in clean)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        candidates.append(
            {
                "package_id": source["id"],
                "package_label": source["label"],
                "source_path": used_path or "",
                "combinations": clean,
            }
        )

    if not candidates:
        fallback = build_fallback_package()
        candidates.append(
            {
                "package_id": "fallback",
                "package_label": _t("\\u0420\\u0435\\u0437\\u0435\\u0440\\u0432\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442"),
                "source_path": "fallback",
                "combinations": fallback,
            }
        )

    return candidates


def build_fallback_package() -> list[list[int]]:
    return [
        [2, 11, 21, 25, 34, 45],
        [4, 12, 19, 27, 38, 48],
        [6, 16, 24, 33, 42, 44],
        [7, 20, 28, 36, 41, 43],
    ]


def _extract_number_score_rows(payload: Any) -> list[tuple[int, float]]:
    rows: list[tuple[int, float]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            number = None
            score = None
            for key in ("number", "num", "ball", "main_number"):
                if key in value:
                    number = _parse_int(value.get(key))
                    if number is not None:
                        break
            for key in ("score", "weighted_score", "final_score", "ensemble_score", "value", "weight"):
                if key in value:
                    try:
                        score = float(value.get(key))
                    except (TypeError, ValueError):
                        score = None
                    if score is not None:
                        break
            if number is not None and score is not None:
                rows.append((number, score))

            for nested in value.values():
                if isinstance(nested, (dict, list, tuple)):
                    walk(nested)

        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, (dict, list, tuple)):
                    walk(item)

    walk(payload)
    return rows


def _load_number_scores_from_csv(path: Path) -> list[tuple[int, float]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return []

    result: list[tuple[int, float]] = []
    for row in rows:
        number = None
        score = None
        for key in ("number", "num", "ball", "main_number"):
            if key in row:
                number = _parse_int(row.get(key))
                if number is not None:
                    break
        for key in ("score", "weighted_score", "final_score", "ensemble_score", "value", "weight"):
            if key in row:
                try:
                    score = float(row.get(key))
                except (TypeError, ValueError):
                    score = None
                if score is not None:
                    break
        if number is not None and score is not None:
            result.append((number, score))
    return result


def load_number_scores() -> dict[int, float]:
    raw: dict[int, list[float]] = {}

    for rel_path in NUMBER_SCORE_PATHS:
        path = ROOT / rel_path
        rows = _load_number_scores_from_csv(path) if path.suffix.lower() == ".csv" else _extract_number_score_rows(_load_json(path))
        for number, score in rows:
            raw.setdefault(number, []).append(score)

    if not raw:
        return {number: 50.0 for number in range(1, TOTAL_NUMBERS + 1)}

    averaged = {number: statistics.mean(scores) for number, scores in raw.items()}
    min_score = min(averaged.values())
    max_score = max(averaged.values())
    span = max_score - min_score

    normalized: dict[int, float] = {}
    for number in range(1, TOTAL_NUMBERS + 1):
        value = averaged.get(number, min_score)
        normalized[number] = 50.0 if span == 0 else ((value - min_score) / span) * 100.0

    return normalized


def load_historical_draw_sets() -> set[tuple[int, ...]]:
    draw_sets: set[tuple[int, ...]] = set()
    for rel_path in HISTORICAL_PATHS:
        path = ROOT / rel_path
        combos = _load_csv_combinations(path)
        for combo in combos:
            draw_sets.add(tuple(combo))
        if draw_sets:
            break
    return draw_sets


def package_unique_numbers(combinations: list[list[int]]) -> set[int]:
    return {number for combo in combinations for number in combo}


def average_pair_overlap(combinations: list[list[int]]) -> float:
    if len(combinations) < 2:
        return 0.0
    overlaps = []
    for left, right in itertools.combinations(combinations, 2):
        overlaps.append(len(set(left).intersection(right)))
    return statistics.mean(overlaps) if overlaps else 0.0


def max_pair_overlap(combinations: list[list[int]]) -> int:
    if len(combinations) < 2:
        return 0
    return max(len(set(left).intersection(right)) for left, right in itertools.combinations(combinations, 2))


def repeated_numbers_count(combinations: list[list[int]]) -> int:
    counts: dict[int, int] = {}
    for combo in combinations:
        for number in combo:
            counts[number] = counts.get(number, 0) + 1
    return sum(max(0, count - 1) for count in counts.values())


def score_model_strength(combinations: list[list[int]], number_scores: dict[int, float]) -> float:
    numbers = [number for combo in combinations for number in combo]
    if not numbers:
        return 0.0
    return max(0.0, min(100.0, statistics.mean(number_scores.get(number, 50.0) for number in numbers)))


def _combo_quality(combo: list[int]) -> float:
    even_count = sum(1 for number in combo if number % 2 == 0)
    low = sum(1 for number in combo if 1 <= number <= 16)
    mid = sum(1 for number in combo if 17 <= number <= 33)
    high = sum(1 for number in combo if 34 <= number <= 49)

    even_score = 100.0 - abs(even_count - 3) * 18.0
    spread_score = 100.0 - (abs(low - 2) + abs(mid - 2) + abs(high - 2)) * 12.0
    range_score = min(100.0, max(0.0, (max(combo) - min(combo)) / 40.0 * 100.0))

    return max(0.0, min(100.0, even_score * 0.40 + spread_score * 0.40 + range_score * 0.20))


def score_combination_quality(combinations: list[list[int]]) -> float:
    if not combinations:
        return 0.0

    combo_quality = statistics.mean(_combo_quality(combo) for combo in combinations)
    overlap = average_pair_overlap(combinations)
    overlap_penalty = min(35.0, overlap * 10.0)
    repeat_penalty = min(25.0, repeated_numbers_count(combinations) * 1.8)

    return max(0.0, min(100.0, combo_quality - overlap_penalty - repeat_penalty))


def score_anti_zero(combinations: list[list[int]]) -> float:
    unique_count = len(package_unique_numbers(combinations))
    risk = calculate_empty_risk(unique_count)
    return max(0.0, min(100.0, risk["at_least_one_hit_percent"]))


def score_historical_safety(combinations: list[list[int]], historical_sets: set[tuple[int, ...]]) -> tuple[float, int]:
    exact_matches = sum(1 for combo in combinations if tuple(combo) in historical_sets)
    score = max(0.0, 100.0 - exact_matches * 40.0)
    return score, exact_matches


def score_package(candidate: dict[str, Any], number_scores: dict[int, float], historical_sets: set[tuple[int, ...]]) -> dict[str, Any]:
    combinations = _dedupe_combinations(candidate.get("combinations", []))
    unique_count = len(package_unique_numbers(combinations))
    risk = calculate_empty_risk(unique_count)

    model_score = score_model_strength(combinations, number_scores)
    quality_score = score_combination_quality(combinations)
    anti_zero_score = score_anti_zero(combinations)
    safety_score, exact_matches = score_historical_safety(combinations, historical_sets)

    mode_scores = {}
    for mode, weights in MODE_WEIGHTS.items():
        score = (
            model_score * weights["model"]
            + quality_score * weights["quality"]
            + anti_zero_score * weights["anti_zero"]
            + safety_score * weights["safety"]
        )
        mode_scores[mode] = round(score, 3)

    return {
        "package_id": candidate.get("package_id", ""),
        "package_label": candidate.get("package_label", ""),
        "source_path": candidate.get("source_path", ""),
        "combinations": combinations,
        "total_combinations": len(combinations),
        "unique_covered_numbers": unique_count,
        "repeated_numbers_count": repeated_numbers_count(combinations),
        "average_overlap": round(average_pair_overlap(combinations), 3),
        "max_overlap": max_pair_overlap(combinations),
        "empty_risk_percent": round(risk["empty_risk_percent"], 6),
        "at_least_one_hit_percent": round(risk["at_least_one_hit_percent"], 6),
        "model_strength_score": round(model_score, 3),
        "combination_quality_score": round(quality_score, 3),
        "anti_zero_score": round(anti_zero_score, 3),
        "historical_safety_score": round(safety_score, 3),
        "historical_exact_matches": exact_matches,
        "mode_scores": mode_scores,
    }


def select_recommendations(scored_packages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    recommendations: dict[str, dict[str, Any]] = {}
    for mode in MODE_WEIGHTS:
        recommendations[mode] = max(scored_packages, key=lambda item: item["mode_scores"].get(mode, 0.0))
    return recommendations


def build_selector_model() -> dict[str, Any]:
    number_scores = load_number_scores()
    historical_sets = load_historical_draw_sets()
    candidates = load_candidate_packages()
    scored = [score_package(candidate, number_scores, historical_sets) for candidate in candidates]

    recommendations = select_recommendations(scored)
    balanced = recommendations.get("balanced", scored[0])

    return {
        "step": 89,
        "title_bg": _t("\\u0424\\u0438\\u043d\\u0430\\u043b\\u0435\\u043d \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0438\\u0437\\u0431\\u043e\\u0440"),
        "safe_note_bg": _t("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0438\\u0437\\u0431\\u043e\\u0440 \\u043d\\u0430 \\u043f\\u0430\\u043a\\u0435\\u0442, \\u043d\\u0435 \\u043f\\u0440\\u043e\\u0433\\u043d\\u043e\\u0437\\u0430 \\u0438 \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430."),
        "candidate_count": len(scored),
        "mode_weights": MODE_WEIGHTS,
        "mode_labels": MODE_LABELS,
        "mode_descriptions": MODE_DESCRIPTIONS,
        "packages": scored,
        "recommendations": recommendations,
        "balanced_recommendation": balanced,
    }


def save_selector_outputs(model: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "step": model["step"],
        "title_bg": model["title_bg"],
        "candidate_count": model["candidate_count"],
        "balanced_package": model["balanced_recommendation"]["package_label"],
        "balanced_score": model["balanced_recommendation"]["mode_scores"].get("balanced", 0.0),
        "conservative_package": model["recommendations"]["conservative"]["package_label"],
        "aggressive_package": model["recommendations"]["aggressive"]["package_label"],
        "safe_note_bg": model["safe_note_bg"],
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with ANALYSIS_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "package_label",
            "total_combinations",
            "unique_covered_numbers",
            "empty_risk_percent",
            "at_least_one_hit_percent",
            "model_strength_score",
            "combination_quality_score",
            "anti_zero_score",
            "historical_safety_score",
            "balanced_score",
            "conservative_score",
            "aggressive_score",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for package in model["packages"]:
            writer.writerow(
                {
                    "package_label": package["package_label"],
                    "total_combinations": package["total_combinations"],
                    "unique_covered_numbers": package["unique_covered_numbers"],
                    "empty_risk_percent": package["empty_risk_percent"],
                    "at_least_one_hit_percent": package["at_least_one_hit_percent"],
                    "model_strength_score": package["model_strength_score"],
                    "combination_quality_score": package["combination_quality_score"],
                    "anti_zero_score": package["anti_zero_score"],
                    "historical_safety_score": package["historical_safety_score"],
                    "balanced_score": package["mode_scores"].get("balanced", 0.0),
                    "conservative_score": package["mode_scores"].get("conservative", 0.0),
                    "aggressive_score": package["mode_scores"].get("aggressive", 0.0),
                }
            )

    balanced = model["balanced_recommendation"]
    md_lines = [
        f"# {model['title_bg']}",
        "",
        f"- {_t('\\u041f\\u0440\\u0435\\u0433\\u043b\\u0435\\u0434\\u0430\\u043d\\u0438 \\u043f\\u0430\\u043a\\u0435\\u0442\\u0438')}: **{model['candidate_count']}**",
        f"- {_t('\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0438\\u0437\\u0431\\u043e\\u0440')}: **{balanced['package_label']}**",
        f"- {_t('\\u041a\\u0440\\u0430\\u0439\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430')}: **{balanced['mode_scores'].get('balanced', 0.0):.2f}**",
        f"- {_t('\\u041f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430')}: **{balanced['unique_covered_numbers']}**",
        f"- {_t('\\u0420\\u0438\\u0441\\u043a \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442')}: **{balanced['empty_risk_percent']:.2f}%**",
        "",
        model["safe_note_bg"],
    ]
    SUMMARY_MD_PATH.write_text("\\n".join(md_lines) + "\\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    model = build_selector_model()
    save_selector_outputs(model)
    return model

# STEP90_SELECTOR_SOURCE_EXPANSION_INTEGRATION_START
_load_candidate_packages_step89_base = load_candidate_packages

def load_candidate_packages():
    try:
        from src.v90_selector_source_expansion_engine import load_expanded_candidate_packages
        expanded_candidates = load_expanded_candidate_packages()
        if expanded_candidates:
            return expanded_candidates
    except Exception:
        pass
    return _load_candidate_packages_step89_base()
# STEP90_SELECTOR_SOURCE_EXPANSION_INTEGRATION_END
