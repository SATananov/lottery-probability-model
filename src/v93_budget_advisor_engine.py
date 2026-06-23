from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any

from src.v91_budget_aware_system_builder_engine import (
    DEFAULT_PRICE_PER_COMBINATION,
    DRAW_SIZE,
    TOTAL_NUMBERS,
    build_and_save as build_step91,
    build_core_pool,
    build_custom_system,
    calculate_empty_risk,
    combination_pairs,
    combination_triples,
    load_number_scores,
    load_step89_balanced_package,
    safe_comb,
    unique_numbers,
)
from src.v92_system_strategy_backtest_center_engine import (
    _efficiency_score,
    _historical_score,
    evaluate_package,
    load_historical_draws,
)

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v93" / "v93_budget_advisor_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v93_budget_advisor_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v93_budget_advisor_summary.md"
SCENARIOS_CSV_PATH = ROOT / "reports" / "v93_budget_advisor_scenarios.csv"
RECOMMENDED_CSV_PATH = ROOT / "reports" / "v93_budget_advisor_recommended_combinations.csv"

STEP91_MODEL_PATH = ROOT / "models" / "v91" / "v91_budget_aware_system_builder_model.json"

SAFE_NOTE_BG = (
    "Това е бюджетен статистически съветник за структура на фиш. "
    "Не е прогноза, не е гаранция и не доказва бъдещ резултат. "
    "Използва текущите Step 89/91/92 резултати, за да предложи разумно разпределение на бюджета."
)

PREFERENCE_LABELS = {
    "auto": "Автоматичен избор",
    "protective": "По-защитен фиш",
    "system": "Системен фиш",
    "hybrid": "Хибриден подход",
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _dedupe_combinations(combinations: list[list[int]]) -> list[list[int]]:
    result: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for combo in combinations:
        clean = sorted({int(number) for number in combo if 1 <= int(number) <= TOTAL_NUMBERS})
        if len(clean) != DRAW_SIZE:
            continue
        key = tuple(clean)
        if key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in sorted(numbers))


def _combination_text(combo: list[int]) -> str:
    return ", ".join(str(number) for number in combo)


def _floor_combinations(budget_eur: float, price_per_combination: float) -> int:
    if price_per_combination <= 0:
        return 0
    return max(0, int(math.floor((float(budget_eur) + 1e-9) / float(price_per_combination))))


def _load_step91_options() -> list[dict[str, Any]]:
    payload = _load_json(STEP91_MODEL_PATH)
    if not isinstance(payload, dict) or not payload.get("options"):
        payload = build_step91()
    options = payload.get("options", []) if isinstance(payload, dict) else []
    return [option for option in options if isinstance(option, dict)]


def _option_combinations(option: dict[str, Any]) -> list[list[int]]:
    return _dedupe_combinations(option.get("combinations", []) or [])


def _base_starred_combinations() -> list[list[int]]:
    step89 = load_step89_balanced_package()
    return _dedupe_combinations(step89.get("combinations", []) or [])


def _base_starred_label() -> str:
    step89 = load_step89_balanced_package()
    return str(step89.get("label") or "Защитен фиш с широко покритие")


def _candidate_from_combinations(
    *,
    candidate_id: str,
    strategy_label: str,
    strategy_type: str,
    source_label: str,
    combinations: list[list[int]],
    price_per_combination: float,
    budget_eur: float,
    preference: str,
    notes: str,
    draws: list[dict[str, Any]],
    system_score: float = 0.0,
) -> dict[str, Any]:
    clean = _dedupe_combinations(combinations)
    count = len(clean)
    cost = round(count * float(price_per_combination), 2)
    unique = len(unique_numbers(clean))
    risk = calculate_empty_risk(unique)
    metrics = evaluate_package(clean, draws) if draws else {
        "draws_tested": 0,
        "average_best_hits": 0.0,
        "max_best_hits": 0,
        "empty_rate_percent": round(risk["empty_risk_percent"], 6),
        "at_least_2_percent": 0.0,
        "at_least_3_percent": 0.0,
        "at_least_4_percent": 0.0,
        "at_least_5_percent": 0.0,
        "exact_6_count": 0,
        "exact_6_percent": 0.0,
    }
    historical_score = _historical_score(metrics, cost)
    efficiency_score = _efficiency_score(metrics, count, cost)
    utilization_percent = round((cost / budget_eur * 100.0) if budget_eur > 0 else 0.0, 3)
    remaining_budget = round(max(0.0, budget_eur - cost), 2)
    covered_pairs = {pair for combo in clean for pair in combination_pairs(combo)}
    covered_triples = {triple for combo in clean for triple in combination_triples(combo)}
    possible_pairs = safe_comb(unique, 2)
    possible_triples = safe_comb(unique, 3)

    preference_bonus = 0.0
    if preference == "protective" and strategy_type in {"Широк фиш", "Хибрид"}:
        preference_bonus += 7.0
    if preference == "system" and strategy_type in {"Пълна система", "Редуцирана система"}:
        preference_bonus += 8.0
    if preference == "hybrid" and strategy_type == "Хибрид":
        preference_bonus += 9.0

    budget_is_small = budget_eur <= 10.80
    unused_penalty = max(0.0, budget_eur - cost) / max(budget_eur, 1.0) * (3.0 if budget_is_small else 11.0)
    empty_weight = 0.24 if preference == "protective" else 0.16
    utilization_bonus = min(100.0, utilization_percent) * (0.045 if budget_is_small else 0.085)

    advisor_score = round(
        historical_score * 0.62
        + efficiency_score * 0.55
        + float(system_score) * 0.08
        + utilization_bonus
        + preference_bonus
        - float(metrics.get("empty_rate_percent", risk["empty_risk_percent"])) * empty_weight
        - unused_penalty,
        3,
    )

    return {
        "candidate_id": candidate_id,
        "strategy_label": strategy_label,
        "strategy_type": strategy_type,
        "source_label": source_label,
        "notes_bg": notes,
        "budget_eur": round(float(budget_eur), 2),
        "price_per_combination_eur": round(float(price_per_combination), 2),
        "max_budget_combinations": _floor_combinations(budget_eur, price_per_combination),
        "combination_count": count,
        "cost_eur": cost,
        "remaining_budget_eur": remaining_budget,
        "budget_utilization_percent": utilization_percent,
        "unique_covered_numbers": unique,
        "core_numbers": sorted(unique_numbers(clean)),
        "core_numbers_text": _numbers_text(sorted(unique_numbers(clean))),
        "empty_risk_percent": round(float(risk["empty_risk_percent"]), 6),
        "at_least_one_hit_percent": round(float(risk["at_least_one_hit_percent"]), 6),
        "historical_average_best_hits": float(metrics.get("average_best_hits", 0.0)),
        "historical_max_best_hits": int(metrics.get("max_best_hits", 0)),
        "historical_empty_rate_percent": float(metrics.get("empty_rate_percent", risk["empty_risk_percent"])),
        "historical_at_least_2_percent": float(metrics.get("at_least_2_percent", 0.0)),
        "historical_at_least_3_percent": float(metrics.get("at_least_3_percent", 0.0)),
        "historical_at_least_4_percent": float(metrics.get("at_least_4_percent", 0.0)),
        "historical_score": historical_score,
        "budget_efficiency_score": efficiency_score,
        "system_score": round(float(system_score), 3),
        "pair_coverage_percent": round((len(covered_pairs) / possible_pairs * 100.0) if possible_pairs else 0.0, 6),
        "triple_coverage_percent": round((len(covered_triples) / possible_triples * 100.0) if possible_triples else 0.0, 6),
        "advisor_score": advisor_score,
        "combinations": clean,
    }


def _candidate_from_step91_option(
    option: dict[str, Any],
    *,
    budget_eur: float,
    price_per_combination: float,
    preference: str,
    draws: list[dict[str, Any]],
) -> dict[str, Any] | None:
    combinations = _option_combinations(option)
    if not combinations:
        return None
    cost = len(combinations) * price_per_combination
    if cost > budget_eur + 1e-9:
        return None
    mode_label = str(option.get("mode_label") or "Стратегия")
    strategy_type = mode_label
    if mode_label == "Широко покритие":
        strategy_type = "Широк фиш"
    return _candidate_from_combinations(
        candidate_id=str(option.get("option_id") or "step91_option"),
        strategy_label=str(option.get("label") or mode_label),
        strategy_type=strategy_type,
        source_label=str(option.get("source_label") or "Step 91"),
        combinations=combinations,
        price_per_combination=price_per_combination,
        budget_eur=budget_eur,
        preference=preference,
        notes="Готов вариант от Step 91, проверен от Step 92 като стратегия върху историческите тиражи.",
        draws=draws,
        system_score=float(option.get("system_score", 0.0) or 0.0),
    )


def _topup_hybrid_candidate(
    *,
    core_source: str,
    budget_eur: float,
    price_per_combination: float,
    preference: str,
    draws: list[dict[str, Any]],
) -> dict[str, Any] | None:
    slots = _floor_combinations(budget_eur, price_per_combination)
    base = _base_starred_combinations()
    if slots <= len(base):
        return None
    extra_needed = slots - len(base)
    generated = build_custom_system(
        core_source=core_source,
        core_size=9,
        selected_combinations=slots + 8,
        full_system=False,
        price_per_combination=price_per_combination,
    )
    base_keys = {tuple(combo) for combo in base}
    extra: list[list[int]] = []
    for combo in _option_combinations(generated):
        key = tuple(combo)
        if key not in base_keys and key not in {tuple(item) for item in extra}:
            extra.append(combo)
        if len(extra) >= extra_needed:
            break
    combinations = _dedupe_combinations(base + extra)
    if len(combinations) <= len(base):
        return None
    source_names = {
        "protected": "звездния фиш",
        "model": "претеглените моделни числа",
        "hybrid": "звездния фиш и моделното ядро",
    }
    return _candidate_from_combinations(
        candidate_id=f"hybrid_starred_plus_{core_source}_{len(combinations)}",
        strategy_label=f"Звезден фиш + допълнителни системни комбинации ({source_names.get(core_source, core_source)})",
        strategy_type="Хибрид",
        source_label="Step 89 звезден фиш + Step 91 редуцирана система",
        combinations=combinations,
        price_per_combination=price_per_combination,
        budget_eur=budget_eur,
        preference=preference,
        notes="Пази базовия фиш със звездичката и добавя още комбинации според оставащия бюджет.",
        draws=draws,
        system_score=float(generated.get("system_score", 0.0) or 0.0),
    )


def _large_full_system_candidate(
    *,
    core_size: int,
    source: str,
    budget_eur: float,
    price_per_combination: float,
    preference: str,
    draws: list[dict[str, Any]],
) -> dict[str, Any] | None:
    slots = _floor_combinations(budget_eur, price_per_combination)
    possible = safe_comb(core_size, DRAW_SIZE)
    if possible <= 0 or possible > slots or possible > 210:
        return None
    number_scores = load_number_scores()
    historical_sets = set()
    pool = build_core_pool(source, core_size, number_scores)
    if len(pool) != core_size:
        return None
    combinations = [list(combo) for combo in __import__("itertools").combinations(sorted(pool), DRAW_SIZE)]
    label_source = {
        "model": "моделни числа",
        "protected": "числа от звездния фиш",
        "hybrid": "хибридно ядро",
    }.get(source, "моделни числа")
    return _candidate_from_combinations(
        candidate_id=f"full_{source}_core_{core_size}",
        strategy_label=f"Пълна система от {core_size} {label_source}",
        strategy_type="Пълна система",
        source_label="Step 91 ядро + бюджетен съветник",
        combinations=combinations,
        price_per_combination=price_per_combination,
        budget_eur=budget_eur,
        preference=preference,
        notes="Пълна система: играят се всички 6-числови комбинации от избраното ядро.",
        draws=draws,
        system_score=0.0,
    )


def build_budget_advice(
    budget_eur: float = 10.0,
    price_per_combination: float = DEFAULT_PRICE_PER_COMBINATION,
    preference: str = "auto",
) -> dict[str, Any]:
    budget = max(0.0, round(float(budget_eur), 2))
    price = max(0.01, round(float(price_per_combination), 2))
    pref = preference if preference in PREFERENCE_LABELS else "auto"
    max_slots = _floor_combinations(budget, price)
    draws = load_historical_draws()

    candidates: list[dict[str, Any]] = []
    base = _base_starred_combinations()
    base_label = _base_starred_label()

    if max_slots > 0 and base:
        partial_count = min(max_slots, len(base))
        partial_label = base_label if partial_count == len(base) else f"Частичен старт от звездния фиш ({partial_count} комбинации)"
        candidates.append(
            _candidate_from_combinations(
                candidate_id=f"starred_first_{partial_count}",
                strategy_label=partial_label,
                strategy_type="Широк фиш",
                source_label="Step 89 фиш със звездичката",
                combinations=base[:partial_count],
                price_per_combination=price,
                budget_eur=budget,
                preference=pref,
                notes="Използва директно най-доверения фиш със звездичката. При малък бюджет това е най-защитеният старт.",
                draws=draws,
                system_score=71.852 if partial_count == len(base) else 0.0,
            )
        )

    for option in _load_step91_options():
        candidate = _candidate_from_step91_option(option, budget_eur=budget, price_per_combination=price, preference=pref, draws=draws)
        if candidate:
            candidates.append(candidate)

    for source in ("protected", "model", "hybrid"):
        candidate = _topup_hybrid_candidate(
            core_source=source,
            budget_eur=budget,
            price_per_combination=price,
            preference=pref,
            draws=draws,
        )
        if candidate:
            candidates.append(candidate)

    for core_size in (10,):
        for source in ("model", "protected", "hybrid"):
            candidate = _large_full_system_candidate(
                core_size=core_size,
                source=source,
                budget_eur=budget,
                price_per_combination=price,
                preference=pref,
                draws=draws,
            )
            if candidate:
                candidates.append(candidate)

    unique_candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[tuple[int, ...], ...]] = set()
    for candidate in candidates:
        key = tuple(tuple(combo) for combo in candidate.get("combinations", []))
        if key not in seen_keys:
            seen_keys.add(key)
            unique_candidates.append(candidate)

    if pref == "protective":
        unique_candidates.sort(key=lambda row: (-float(row["advisor_score"]), float(row["historical_empty_rate_percent"]), -int(row["unique_covered_numbers"])))
    elif pref == "system":
        unique_candidates.sort(key=lambda row: (-float(row["advisor_score"]), -int(row["combination_count"]), float(row["cost_eur"])))
    else:
        unique_candidates.sort(key=lambda row: (-float(row["advisor_score"]), -float(row["historical_average_best_hits"]), float(row["historical_empty_rate_percent"])))

    recommendation = unique_candidates[0] if unique_candidates else {}
    warning = ""
    if max_slots < 4:
        warning = "Бюджетът е под стандартен 4-комбинационен фиш. Съветникът дава частичен вариант, но покритието е ограничено."
    elif recommendation and recommendation.get("strategy_type") == "Широк фиш" and budget - float(recommendation.get("cost_eur", 0.0)) >= price:
        warning = "Историческият тест запазва широкия фиш като най-стабилен избор; оставащият бюджет може да се използва само ако искаш по-агресивна допълнителна система."

    if recommendation.get("strategy_type") == "Пълна система":
        reason = "Бюджетът позволява пълно системно комбиниране на избраното ядро и този вариант дава най-силен исторически профил сред наличните кандидати."
    elif recommendation.get("strategy_type") == "Хибрид":
        reason = "Препоръката пази фиша със звездичката и използва останалия бюджет за допълнително системно покритие."
    elif recommendation.get("strategy_type") == "Редуцирана система":
        reason = "Препоръката търси по-добра системна структура в рамките на бюджета, без да плаща за пълна система."
    else:
        reason = "Step 92 показа, че при този бюджет най-стабилният практичен избор е широкото покритие от фиша със звездичката."

    return {
        "step": 93,
        "status": "OK" if recommendation else "NO_RECOMMENDATION",
        "title_bg": "Бюджетен съветник",
        "safe_note_bg": SAFE_NOTE_BG,
        "budget_eur": budget,
        "price_per_combination_eur": price,
        "max_budget_combinations": max_slots,
        "preference": pref,
        "preference_label": PREFERENCE_LABELS[pref],
        "starred_package_label": base_label,
        "starred_combinations": base,
        "candidate_count": len(unique_candidates),
        "recommendation": recommendation,
        "candidate_plans": unique_candidates,
        "reason_bg": reason,
        "warning_bg": warning,
        "method_summary_bg": (
            "Съветникът превръща бюджета в максимален брой комбинации, после сравнява фиша със звездичката, "
            "готовите Step 91 системи, хибридни варианти и достъпните пълни системи. "
            "Оценката използва исторически replay показатели от Step 92, празен риск, бюджетна ефективност и използване на бюджета."
        ),
    }


def _scenario_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in model.get("default_scenarios", []):
        rec = scenario.get("recommendation", {}) or {}
        rows.append(
            {
                "budget_eur": scenario.get("budget_eur", 0.0),
                "price_per_combination_eur": scenario.get("price_per_combination_eur", 0.0),
                "max_budget_combinations": scenario.get("max_budget_combinations", 0),
                "strategy_label": rec.get("strategy_label", ""),
                "strategy_type": rec.get("strategy_type", ""),
                "combination_count": rec.get("combination_count", 0),
                "cost_eur": rec.get("cost_eur", 0.0),
                "remaining_budget_eur": rec.get("remaining_budget_eur", 0.0),
                "unique_covered_numbers": rec.get("unique_covered_numbers", 0),
                "historical_average_best_hits": rec.get("historical_average_best_hits", 0.0),
                "historical_empty_rate_percent": rec.get("historical_empty_rate_percent", 0.0),
                "historical_at_least_3_percent": rec.get("historical_at_least_3_percent", 0.0),
                "advisor_score": rec.get("advisor_score", 0.0),
            }
        )
    return rows


def build_budget_advisor_model() -> dict[str, Any]:
    default_budgets = [3.60, 7.20, 10.80, 25.20, 75.60, 189.00]
    scenarios = [build_budget_advice(budget, DEFAULT_PRICE_PER_COMBINATION, "auto") for budget in default_budgets]
    current = build_budget_advice(10.00, DEFAULT_PRICE_PER_COMBINATION, "auto")
    return {
        "step": 93,
        "status": "OK",
        "title_bg": "Бюджетен съветник",
        "safe_note_bg": SAFE_NOTE_BG,
        "default_price_per_combination_eur": DEFAULT_PRICE_PER_COMBINATION,
        "default_scenarios": scenarios,
        "current_reference_advice": current,
        "method_summary_bg": current.get("method_summary_bg", ""),
    }


def save_budget_advisor_outputs(model: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    current = model.get("current_reference_advice", {}) or {}
    recommendation = current.get("recommendation", {}) or {}
    summary = {
        "step": 93,
        "status": model.get("status", "OK"),
        "title_bg": model.get("title_bg", "Бюджетен съветник"),
        "default_budget_eur": current.get("budget_eur", 10.0),
        "default_price_per_combination_eur": current.get("price_per_combination_eur", DEFAULT_PRICE_PER_COMBINATION),
        "default_max_combinations": current.get("max_budget_combinations", 0),
        "recommended_strategy": recommendation.get("strategy_label", ""),
        "recommended_type": recommendation.get("strategy_type", ""),
        "recommended_combinations": recommendation.get("combination_count", 0),
        "recommended_cost_eur": recommendation.get("cost_eur", 0.0),
        "recommended_unique_numbers": recommendation.get("unique_covered_numbers", 0),
        "recommended_advisor_score": recommendation.get("advisor_score", 0.0),
        "safe_note_bg": SAFE_NOTE_BG,
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with SCENARIOS_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "budget_eur",
            "price_per_combination_eur",
            "max_budget_combinations",
            "strategy_label",
            "strategy_type",
            "combination_count",
            "cost_eur",
            "remaining_budget_eur",
            "unique_covered_numbers",
            "historical_average_best_hits",
            "historical_empty_rate_percent",
            "historical_at_least_3_percent",
            "advisor_score",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_scenario_rows(model))

    with RECOMMENDED_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["combination_index", "numbers", "n1", "n2", "n3", "n4", "n5", "n6"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for index, combo in enumerate(recommendation.get("combinations", []) or [], start=1):
            writer.writerow(
                {
                    "combination_index": index,
                    "numbers": _combination_text(combo),
                    "n1": combo[0],
                    "n2": combo[1],
                    "n3": combo[2],
                    "n4": combo[3],
                    "n5": combo[4],
                    "n6": combo[5],
                }
            )

    lines = [
        "# Бюджетен съветник",
        "",
        f"- Стандартен примерен бюджет: **{float(current.get('budget_eur', 0.0)):.2f} EUR**",
        f"- Максимален брой комбинации: **{int(current.get('max_budget_combinations', 0))}**",
        f"- Препоръка: **{recommendation.get('strategy_label', '-')}**",
        f"- Тип: **{recommendation.get('strategy_type', '-')}**",
        f"- Комбинации: **{int(recommendation.get('combination_count', 0))}**",
        f"- Цена: **{float(recommendation.get('cost_eur', 0.0)):.2f} EUR**",
        f"- Уникални числа: **{int(recommendation.get('unique_covered_numbers', 0))}**",
        f"- Оценка: **{float(recommendation.get('advisor_score', 0.0)):.3f}**",
        "",
        SAFE_NOTE_BG,
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    model = build_budget_advisor_model()
    save_budget_advisor_outputs(model)
    return model


if __name__ == "__main__":
    result = build_and_save()
    current = result.get("current_reference_advice", {})
    rec = current.get("recommendation", {}) or {}
    print("STEP_93_STATUS", result.get("status", "UNKNOWN"))
    print("DEFAULT_BUDGET", current.get("budget_eur", 0.0))
    print("MAX_COMBINATIONS", current.get("max_budget_combinations", 0))
    print("RECOMMENDED", rec.get("strategy_type", "-"), rec.get("combination_count", 0), f"{float(rec.get('advisor_score', 0.0)):.3f}")
