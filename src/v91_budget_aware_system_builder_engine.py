from __future__ import annotations

import csv
import itertools
import json
import math
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

TOTAL_NUMBERS = 49
DRAW_SIZE = 6
DEFAULT_PRICE_PER_COMBINATION = 0.90
SECONDARY_PRICE_PER_COMBINATION = 0.80

MODEL_PATH = ROOT / "models" / "v91" / "v91_budget_aware_system_builder_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v91_budget_aware_system_builder_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v91_budget_aware_system_builder_summary.md"
OPTIONS_CSV_PATH = ROOT / "reports" / "v91_budget_aware_system_options.csv"
RECOMMENDED_CSV_PATH = ROOT / "reports" / "v91_recommended_system_combinations.csv"

WEIGHTED_SCORE_PATHS = (
    "reports/v66_weighted_smart_ensemble_scores.csv",
    "models/v66/v66_weighted_smart_ensemble_model.json",
    "reports/v58_smart_ensemble_scores_sample.csv",
)

STEP89_MODEL_PATH = ROOT / "models" / "v89" / "v89_final_statistical_portfolio_selector_model.json"
HISTORICAL_PATHS = (
    "data/v41_canonical_draw_events.csv",
    "data/v40_normalized_draw_events.csv",
    "data/historical_draws.csv",
)


def safe_comb(n: int, k: int) -> int:
    if n < 0 or k < 0 or k > n:
        return 0
    try:
        return math.comb(n, k)
    except ValueError:
        return 0


def _parse_int(value: Any) -> int | None:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= TOTAL_NUMBERS else None


def normalize_combination(value: Any) -> list[int]:
    if isinstance(value, str):
        raw_values = value.replace(";", ",").replace("|", ",").split(",")
        if len(raw_values) == 1:
            raw_values = value.split()
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

    clean = sorted(numbers)
    return clean if len(clean) == DRAW_SIZE else []


def _dedupe_combinations(combinations: list[list[int]]) -> list[list[int]]:
    result: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for combo in combinations:
        clean = normalize_combination(combo)
        key = tuple(clean)
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


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
            for key in (
                "weighted_score_percent",
                "weighted_score",
                "score_percent",
                "score",
                "final_score",
                "ensemble_score",
                "value",
                "weight",
            ):
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
        for key in (
            "weighted_score_percent",
            "weighted_score",
            "score_percent",
            "score",
            "final_score",
            "ensemble_score",
            "value",
            "weight",
        ):
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
    collected: dict[int, list[float]] = {}

    for rel_path in WEIGHTED_SCORE_PATHS:
        path = ROOT / rel_path
        if not path.exists():
            continue
        rows = _load_number_scores_from_csv(path) if path.suffix.lower() == ".csv" else _extract_number_score_rows(_load_json(path))
        for number, score in rows:
            collected.setdefault(number, []).append(float(score))
        if collected:
            break

    if not collected:
        return {number: 50.0 for number in range(1, TOTAL_NUMBERS + 1)}

    averaged = {number: statistics.mean(scores) for number, scores in collected.items()}
    min_score = min(averaged.values())
    max_score = max(averaged.values())
    span = max_score - min_score

    normalized: dict[int, float] = {}
    for number in range(1, TOTAL_NUMBERS + 1):
        value = averaged.get(number, min_score)
        normalized[number] = 50.0 if span == 0 else ((value - min_score) / span) * 100.0
    return normalized


def _extract_combinations_from_payload(payload: Any) -> list[list[int]]:
    results: list[list[int]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for keys in (
                ("n1", "n2", "n3", "n4", "n5", "n6"),
                ("number_1", "number_2", "number_3", "number_4", "number_5", "number_6"),
                ("main_1", "main_2", "main_3", "main_4", "main_5", "main_6"),
            ):
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
                "combinations",
                "candidate_combinations",
                "final_combinations",
            ):
                if key in value:
                    maybe = value.get(key)
                    combo = normalize_combination(maybe)
                    if combo:
                        results.append(combo)
                    elif isinstance(maybe, (dict, list, tuple)):
                        walk(maybe)

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
        for keys in (
            ("n1", "n2", "n3", "n4", "n5", "n6"),
            ("number_1", "number_2", "number_3", "number_4", "number_5", "number_6"),
            ("main_1", "main_2", "main_3", "main_4", "main_5", "main_6"),
        ):
            if all(key in row and str(row.get(key, "")).strip() for key in keys):
                combo = normalize_combination([row.get(key) for key in keys])
                if combo:
                    combinations.append(combo)

        for key in ("numbers", "combination", "selected_numbers", "main_numbers", "ticket_numbers", "field_numbers"):
            if key in row and str(row.get(key, "")).strip():
                combo = normalize_combination(row.get(key))
                if combo:
                    combinations.append(combo)
    return _dedupe_combinations(combinations)


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


def load_step89_balanced_package() -> dict[str, Any]:
    payload = _load_json(STEP89_MODEL_PATH)
    if isinstance(payload, dict):
        package = payload.get("balanced_recommendation") or payload.get("recommendations", {}).get("balanced") or {}
        combinations = _dedupe_combinations(package.get("combinations", []))
        if combinations:
            return {
                "label": package.get("package_label", "Защитен фиш с широко покритие"),
                "combinations": combinations,
                "score": float(package.get("mode_scores", {}).get("balanced", 0.0)),
                "empty_risk_percent": float(package.get("empty_risk_percent", 0.0)),
            }
    return {
        "label": "Защитен фиш с широко покритие",
        "combinations": [
            [7, 12, 25, 26, 34, 42],
            [4, 22, 24, 29, 37, 44],
            [2, 21, 28, 33, 45, 48],
            [11, 20, 23, 27, 38, 41],
        ],
        "score": 0.0,
        "empty_risk_percent": 0.0,
    }


def unique_numbers(combinations: list[list[int]]) -> set[int]:
    return {number for combo in combinations for number in combo}


def calculate_empty_risk(unique_covered_numbers: int) -> dict[str, float]:
    unique = max(0, min(TOTAL_NUMBERS, int(unique_covered_numbers)))
    denominator = safe_comb(TOTAL_NUMBERS, DRAW_SIZE)
    numerator = safe_comb(TOTAL_NUMBERS - unique, DRAW_SIZE)
    empty = numerator / denominator if denominator else 0.0
    return {
        "empty_risk_percent": empty * 100.0,
        "at_least_one_hit_percent": (1.0 - empty) * 100.0,
    }


def combination_pairs(combo: list[int]) -> set[tuple[int, int]]:
    return {tuple(sorted(pair)) for pair in itertools.combinations(combo, 2)}


def combination_triples(combo: list[int]) -> set[tuple[int, int, int]]:
    return {tuple(sorted(triple)) for triple in itertools.combinations(combo, 3)}


def _combo_balance_score(combo: list[int]) -> float:
    if len(combo) != DRAW_SIZE:
        return 0.0
    even_count = sum(1 for number in combo if number % 2 == 0)
    low = sum(1 for number in combo if 1 <= number <= 16)
    mid = sum(1 for number in combo if 17 <= number <= 33)
    high = sum(1 for number in combo if 34 <= number <= 49)
    total_sum = sum(combo)
    number_range = max(combo) - min(combo)

    even_score = 100.0 - abs(even_count - 3) * 16.0
    zone_score = 100.0 - (abs(low - 2) + abs(mid - 2) + abs(high - 2)) * 10.0
    sum_score = 100.0 - min(60.0, abs(total_sum - 150.0) * 0.75)
    range_score = min(100.0, max(0.0, number_range / 40.0 * 100.0))
    return max(0.0, min(100.0, even_score * 0.30 + zone_score * 0.30 + sum_score * 0.25 + range_score * 0.15))


def _model_mean(combo: list[int], number_scores: dict[int, float]) -> float:
    if not combo:
        return 0.0
    return statistics.mean(number_scores.get(number, 50.0) for number in combo)


def _package_model_score(combinations: list[list[int]], number_scores: dict[int, float]) -> float:
    numbers = [number for combo in combinations for number in combo]
    if not numbers:
        return 0.0
    return statistics.mean(number_scores.get(number, 50.0) for number in numbers)


def _package_balance_score(combinations: list[list[int]]) -> float:
    if not combinations:
        return 0.0
    return statistics.mean(_combo_balance_score(combo) for combo in combinations)


def _historical_exact_matches(combinations: list[list[int]], historical_sets: set[tuple[int, ...]]) -> int:
    return sum(1 for combo in combinations if tuple(combo) in historical_sets)


def _select_reduced_combinations(
    pool: list[int],
    target_count: int,
    number_scores: dict[int, float],
    historical_sets: set[tuple[int, ...]],
) -> list[list[int]]:
    all_combinations = [list(combo) for combo in itertools.combinations(sorted(pool), DRAW_SIZE)]
    target = max(1, min(int(target_count), len(all_combinations)))
    selected: list[list[int]] = []
    remaining = all_combinations[:]
    covered_pairs: set[tuple[int, int]] = set()
    covered_triples: set[tuple[int, int, int]] = set()

    while remaining and len(selected) < target:
        best_index = 0
        best_score = -1e9
        for index, combo in enumerate(remaining):
            pairs = combination_pairs(combo)
            triples = combination_triples(combo)
            new_pair_count = len(pairs - covered_pairs)
            new_triple_count = len(triples - covered_triples)
            overlap_penalty = 0.0
            if selected:
                overlap_penalty = statistics.mean(len(set(combo).intersection(other)) for other in selected)
            exact_penalty = 35.0 if tuple(combo) in historical_sets else 0.0
            score = (
                _model_mean(combo, number_scores) * 0.34
                + _combo_balance_score(combo) * 0.26
                + new_pair_count * 2.20
                + new_triple_count * 0.90
                - overlap_penalty * 6.00
                - exact_penalty
            )
            if score > best_score:
                best_score = score
                best_index = index

        chosen = remaining.pop(best_index)
        selected.append(chosen)
        covered_pairs.update(combination_pairs(chosen))
        covered_triples.update(combination_triples(chosen))

    return _dedupe_combinations(selected)


def build_core_pool(source: str, core_size: int, number_scores: dict[int, float]) -> list[int]:
    size = max(DRAW_SIZE, min(13, int(core_size)))
    step89 = load_step89_balanced_package()
    protected_numbers = sorted(unique_numbers(step89["combinations"]), key=lambda n: (-number_scores.get(n, 50.0), n))
    model_numbers = sorted(range(1, TOTAL_NUMBERS + 1), key=lambda n: (-number_scores.get(n, 50.0), n))

    if source == "protected":
        pool = protected_numbers[:size]
    elif source == "hybrid":
        pool = []
        for number in protected_numbers[: max(DRAW_SIZE, size - 3)] + model_numbers:
            if number not in pool:
                pool.append(number)
            if len(pool) >= size:
                break
    else:
        pool = model_numbers[:size]

    return sorted(pool)


def _source_label(source: str) -> str:
    labels = {
        "protected": "Защитно ядро от финалния фиш",
        "model": "Моделно ядро от претеглените сигнали",
        "hybrid": "Хибридно ядро",
    }
    return labels.get(source, "Моделно ядро от претеглените сигнали")


def score_system_option(
    combinations: list[list[int]],
    pool_size: int,
    number_scores: dict[int, float],
    historical_sets: set[tuple[int, ...]],
) -> float:
    if not combinations:
        return 0.0
    model_score = _package_model_score(combinations, number_scores)
    balance_score = _package_balance_score(combinations)
    possible_pairs = safe_comb(pool_size, 2)
    possible_triples = safe_comb(pool_size, 3)
    pair_score = len({pair for combo in combinations for pair in combination_pairs(combo)}) / possible_pairs * 100.0 if possible_pairs else 0.0
    triple_score = len({triple for combo in combinations for triple in combination_triples(combo)}) / possible_triples * 100.0 if possible_triples else 0.0
    safety_score = max(0.0, 100.0 - _historical_exact_matches(combinations, historical_sets) * 35.0)
    return round(model_score * 0.38 + balance_score * 0.22 + pair_score * 0.18 + triple_score * 0.12 + safety_score * 0.10, 3)


def build_system_option(
    *,
    option_id: str,
    label: str,
    source: str,
    pool: list[int],
    mode: str,
    target_count: int | None,
    price_per_combination: float,
    number_scores: dict[int, float],
    historical_sets: set[tuple[int, ...]],
) -> dict[str, Any]:
    possible_count = safe_comb(len(pool), DRAW_SIZE)
    if mode == "full":
        combinations = [list(combo) for combo in itertools.combinations(sorted(pool), DRAW_SIZE)]
        mode_label = "Пълна система"
    else:
        combinations = _select_reduced_combinations(pool, int(target_count or DRAW_SIZE), number_scores, historical_sets)
        mode_label = "Редуцирана система"

    combinations = _dedupe_combinations(combinations)
    selected_count = len(combinations)
    unique_count = len(unique_numbers(combinations))
    risk = calculate_empty_risk(unique_count)
    exact_denominator = safe_comb(TOTAL_NUMBERS, DRAW_SIZE)
    possible_pairs = safe_comb(len(pool), 2)
    possible_triples = safe_comb(len(pool), 3)
    covered_pairs = {pair for combo in combinations for pair in combination_pairs(combo)}
    covered_triples = {triple for combo in combinations for triple in combination_triples(combo)}
    exact_matches = _historical_exact_matches(combinations, historical_sets)

    return {
        "option_id": option_id,
        "label": label,
        "mode": mode,
        "mode_label": mode_label,
        "source": source,
        "source_label": _source_label(source),
        "core_numbers": sorted(pool),
        "core_size": len(pool),
        "combinations": combinations,
        "selected_combinations": selected_count,
        "possible_full_combinations": possible_count,
        "pool_coverage_percent": round((selected_count / possible_count * 100.0) if possible_count else 0.0, 6),
        "cost_eur": round(selected_count * float(price_per_combination), 2),
        "cost_eur_at_080": round(selected_count * SECONDARY_PRICE_PER_COMBINATION, 2),
        "cost_eur_at_090": round(selected_count * DEFAULT_PRICE_PER_COMBINATION, 2),
        "unique_covered_numbers": unique_count,
        "empty_risk_percent": round(risk["empty_risk_percent"], 6),
        "at_least_one_hit_percent": round(risk["at_least_one_hit_percent"], 6),
        "exact_combination_probability_percent": round((selected_count / exact_denominator * 100.0) if exact_denominator else 0.0, 9),
        "pair_coverage_percent": round((len(covered_pairs) / possible_pairs * 100.0) if possible_pairs else 0.0, 6),
        "triple_coverage_percent": round((len(covered_triples) / possible_triples * 100.0) if possible_triples else 0.0, 6),
        "model_strength_score": round(_package_model_score(combinations, number_scores), 3),
        "balance_score": round(_package_balance_score(combinations), 3),
        "historical_exact_matches": exact_matches,
        "system_score": score_system_option(combinations, len(pool), number_scores, historical_sets),
    }


def build_current_reference(number_scores: dict[int, float], historical_sets: set[tuple[int, ...]]) -> dict[str, Any]:
    step89 = load_step89_balanced_package()
    combinations = _dedupe_combinations(step89["combinations"])
    unique_count = len(unique_numbers(combinations))
    risk = calculate_empty_risk(unique_count)
    exact_denominator = safe_comb(TOTAL_NUMBERS, DRAW_SIZE)
    return {
        "option_id": "step89_reference",
        "label": step89["label"],
        "mode": "reference",
        "mode_label": "Широко покритие",
        "source": "step89",
        "source_label": "Финален статистически избор",
        "core_numbers": sorted(unique_numbers(combinations)),
        "core_size": unique_count,
        "combinations": combinations,
        "selected_combinations": len(combinations),
        "possible_full_combinations": safe_comb(unique_count, DRAW_SIZE),
        "pool_coverage_percent": round((len(combinations) / safe_comb(unique_count, DRAW_SIZE) * 100.0) if safe_comb(unique_count, DRAW_SIZE) else 0.0, 6),
        "cost_eur": round(len(combinations) * DEFAULT_PRICE_PER_COMBINATION, 2),
        "cost_eur_at_080": round(len(combinations) * SECONDARY_PRICE_PER_COMBINATION, 2),
        "cost_eur_at_090": round(len(combinations) * DEFAULT_PRICE_PER_COMBINATION, 2),
        "unique_covered_numbers": unique_count,
        "empty_risk_percent": round(risk["empty_risk_percent"], 6),
        "at_least_one_hit_percent": round(risk["at_least_one_hit_percent"], 6),
        "exact_combination_probability_percent": round((len(combinations) / exact_denominator * 100.0) if exact_denominator else 0.0, 9),
        "pair_coverage_percent": 0.0,
        "triple_coverage_percent": 0.0,
        "model_strength_score": round(_package_model_score(combinations, number_scores), 3),
        "balance_score": round(_package_balance_score(combinations), 3),
        "historical_exact_matches": _historical_exact_matches(combinations, historical_sets),
        "system_score": round(float(step89.get("score", 0.0)), 3),
    }


def build_custom_system(
    *,
    core_source: str = "protected",
    core_size: int = 9,
    selected_combinations: int = 4,
    full_system: bool = False,
    price_per_combination: float = DEFAULT_PRICE_PER_COMBINATION,
) -> dict[str, Any]:
    number_scores = load_number_scores()
    historical_sets = load_historical_draw_sets()
    pool = build_core_pool(core_source, core_size, number_scores)
    mode = "full" if full_system else "reduced"
    label = f"{_source_label(core_source)} — {'пълна система' if full_system else 'редуцирана система'}"
    return build_system_option(
        option_id="custom_system",
        label=label,
        source=core_source,
        pool=pool,
        mode=mode,
        target_count=selected_combinations,
        price_per_combination=price_per_combination,
        number_scores=number_scores,
        historical_sets=historical_sets,
    )


def build_budget_aware_system_model() -> dict[str, Any]:
    number_scores = load_number_scores()
    historical_sets = load_historical_draw_sets()

    options: list[dict[str, Any]] = [build_current_reference(number_scores, historical_sets)]

    for core_size in (7, 8, 9):
        pool = build_core_pool("model", core_size, number_scores)
        options.append(
            build_system_option(
                option_id=f"full_model_core_{core_size}",
                label=f"Пълна система от {core_size} моделни числа",
                source="model",
                pool=pool,
                mode="full",
                target_count=None,
                price_per_combination=DEFAULT_PRICE_PER_COMBINATION,
                number_scores=number_scores,
                historical_sets=historical_sets,
            )
        )

    for source in ("protected", "model", "hybrid"):
        for target in (4, 8, 12, 16):
            pool = build_core_pool(source, 9, number_scores)
            options.append(
                build_system_option(
                    option_id=f"reduced_{source}_core_9_{target}",
                    label=f"Редуцирана система: {_source_label(source)}, 9 числа, {target} комбинации",
                    source=source,
                    pool=pool,
                    mode="reduced",
                    target_count=target,
                    price_per_combination=DEFAULT_PRICE_PER_COMBINATION,
                    number_scores=number_scores,
                    historical_sets=historical_sets,
                )
            )

    practical_candidates = [option for option in options if option["mode"] == "reduced" and option["selected_combinations"] == 4]
    practical = max(practical_candidates, key=lambda item: item["system_score"]) if practical_candidates else options[0]
    best_under_10_eur = max(
        [option for option in options if option.get("cost_eur_at_090", 999.0) <= 10.0 and option["mode"] != "reference"],
        key=lambda item: item["system_score"],
        default=practical,
    )

    return {
        "step": 91,
        "status": "OK",
        "title_bg": "Системни фишове според бюджет",
        "safe_note_bg": "Това е статистически метод за структуриране на фишове. Не е прогноза и не е гаранция за печалба.",
        "price_per_combination_eur": DEFAULT_PRICE_PER_COMBINATION,
        "total_lottery_combinations": safe_comb(TOTAL_NUMBERS, DRAW_SIZE),
        "method_summary_bg": "Слоят сравнява широко покритие, пълна система и редуцирана система. Целта е да се избере разумен компромис между цена, покритие и моделни сигнали.",
        "options": options,
        "option_count": len(options),
        "practical_recommendation": practical,
        "best_under_10_eur": best_under_10_eur,
    }


def save_budget_aware_outputs(model: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    practical = model["practical_recommendation"]
    summary = {
        "step": model["step"],
        "status": model["status"],
        "title_bg": model["title_bg"],
        "option_count": model["option_count"],
        "practical_recommendation": practical["label"],
        "practical_core_numbers": practical["core_numbers"],
        "practical_selected_combinations": practical["selected_combinations"],
        "practical_cost_eur_at_090": practical["cost_eur_at_090"],
        "practical_system_score": practical["system_score"],
        "safe_note_bg": model["safe_note_bg"],
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with OPTIONS_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "label",
            "mode_label",
            "source_label",
            "core_size",
            "core_numbers",
            "selected_combinations",
            "possible_full_combinations",
            "pool_coverage_percent",
            "cost_eur_at_080",
            "cost_eur_at_090",
            "unique_covered_numbers",
            "empty_risk_percent",
            "exact_combination_probability_percent",
            "pair_coverage_percent",
            "triple_coverage_percent",
            "model_strength_score",
            "balance_score",
            "historical_exact_matches",
            "system_score",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for option in model["options"]:
            row = {key: option.get(key, "") for key in fieldnames}
            row["core_numbers"] = ", ".join(str(number) for number in option.get("core_numbers", []))
            writer.writerow(row)

    with RECOMMENDED_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["combination_index", "numbers", "n1", "n2", "n3", "n4", "n5", "n6"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for index, combo in enumerate(practical.get("combinations", []), start=1):
            writer.writerow(
                {
                    "combination_index": index,
                    "numbers": ", ".join(str(number) for number in combo),
                    "n1": combo[0],
                    "n2": combo[1],
                    "n3": combo[2],
                    "n4": combo[3],
                    "n5": combo[4],
                    "n6": combo[5],
                }
            )

    lines = [
        f"# {model['title_bg']}",
        "",
        f"- Разгледани варианти: **{model['option_count']}**",
        f"- Практическа препоръка: **{practical['label']}**",
        f"- Ядро: **{', '.join(str(number) for number in practical['core_numbers'])}**",
        f"- Комбинации: **{practical['selected_combinations']}**",
        f"- Цена при 0.90 EUR: **{practical['cost_eur_at_090']:.2f} EUR**",
        f"- Покритие на системата: **{practical['pool_coverage_percent']:.2f}%**",
        f"- Оценка на системата: **{practical['system_score']:.2f}**",
        "",
        model["safe_note_bg"],
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    model = build_budget_aware_system_model()
    save_budget_aware_outputs(model)
    return model
