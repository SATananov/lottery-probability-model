from __future__ import annotations

import csv
import itertools
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

TOTAL_NUMBERS = 49
DRAW_SIZE = 6
DEFAULT_RANDOM_TRIALS = 25

MODEL_PATH = ROOT / "models" / "v92" / "v92_system_strategy_backtest_center_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v92_system_strategy_backtest_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v92_system_strategy_backtest_summary.md"
RESULTS_CSV_PATH = ROOT / "reports" / "v92_strategy_backtest_results.csv"
DISTRIBUTION_CSV_PATH = ROOT / "reports" / "v92_strategy_match_distribution.csv"
BASELINE_CSV_PATH = ROOT / "reports" / "v92_random_baseline_summary.csv"

STEP91_MODEL_PATH = ROOT / "models" / "v91" / "v91_budget_aware_system_builder_model.json"
HISTORICAL_PATHS = (
    ROOT / "data" / "v41_canonical_draw_events.csv",
    ROOT / "data" / "v40_normalized_draw_events.csv",
    ROOT / "data" / "historical_draws.csv",
)

SAFE_NOTE_BG = (
    "Това е исторически replay на текущите стратегии и текущите им комбинации. "
    "Не е walk-forward обучение, не е прогноза и не е гаранция за печалба. "
    "Използва се само за сравнение на структура, риск и поведение върху минали тиражи."
)


def safe_comb(n: int, k: int) -> int:
    if n < 0 or k < 0 or k > n:
        return 0
    return math.comb(n, k)


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


def _mask(numbers: list[int]) -> int:
    value = 0
    for number in numbers:
        if 1 <= int(number) <= TOTAL_NUMBERS:
            value |= 1 << (int(number) - 1)
    return value


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in sorted(numbers))


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _load_step91_model() -> dict[str, Any]:
    payload = _load_json(STEP91_MODEL_PATH)
    if isinstance(payload, dict) and payload.get("options"):
        return payload

    from src.v91_budget_aware_system_builder_engine import build_and_save

    return build_and_save()


def _extract_row_combination(row: dict[str, Any]) -> list[int]:
    for keys in (
        ("n1", "n2", "n3", "n4", "n5", "n6"),
        ("number_1", "number_2", "number_3", "number_4", "number_5", "number_6"),
        ("main_1", "main_2", "main_3", "main_4", "main_5", "main_6"),
    ):
        if all(key in row for key in keys):
            combo = normalize_combination([row.get(key) for key in keys])
            if combo:
                return combo
    for key in ("numbers", "combination", "main_numbers", "ticket_numbers"):
        if row.get(key):
            combo = normalize_combination(row.get(key))
            if combo:
                return combo
    return []


def load_historical_draws() -> list[dict[str, Any]]:
    for path in HISTORICAL_PATHS:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
        except Exception:
            continue

        draws: list[dict[str, Any]] = []
        for index, row in enumerate(rows, start=1):
            numbers = _extract_row_combination(row)
            if not numbers:
                continue
            draw_id = row.get("draw_event_id") or row.get("draw_id") or row.get("source_draw_id") or str(index)
            draws.append(
                {
                    "index": index,
                    "draw_id": str(draw_id),
                    "year": str(row.get("year", "")).strip(),
                    "date": str(row.get("date", "")).strip(),
                    "numbers": numbers,
                    "mask": _mask(numbers),
                }
            )
        if draws:
            return draws
    return []


def _strategy_label(option: dict[str, Any]) -> str:
    label = str(option.get("label") or option.get("option_id") or "Стратегия")
    return label.replace("  ", " ").strip()


def _strategy_type(option: dict[str, Any]) -> str:
    mode_label = str(option.get("mode_label") or option.get("mode") or "-")
    source_label = str(option.get("source_label") or option.get("source") or "-")
    return f"{mode_label} / {source_label}"


def _option_combinations(option: dict[str, Any]) -> list[list[int]]:
    return _dedupe_combinations(option.get("combinations") or [])


def _hit_distribution_percent(counts: Counter[int], draws_count: int, threshold: int) -> float:
    if not draws_count:
        return 0.0
    hits = sum(value for bucket, value in counts.items() if int(bucket) >= threshold)
    return hits / draws_count * 100.0


def evaluate_package(combinations: list[list[int]], draws: list[dict[str, Any]]) -> dict[str, Any]:
    clean_combinations = _dedupe_combinations(combinations)
    combo_masks = [_mask(combo) for combo in clean_combinations]
    counts: Counter[int] = Counter()
    total_best_hits = 0
    total_all_row_hits = 0
    best_seen = 0

    for draw in draws:
        draw_mask = int(draw["mask"])
        if combo_masks:
            row_hits = [(draw_mask & combo_mask).bit_count() for combo_mask in combo_masks]
            best_hits = max(row_hits)
            total_hits = sum(row_hits)
        else:
            best_hits = 0
            total_hits = 0
        counts[best_hits] += 1
        total_best_hits += best_hits
        total_all_row_hits += total_hits
        if best_hits > best_seen:
            best_seen = best_hits

    draws_count = len(draws)
    distribution = {str(hit): int(counts.get(hit, 0)) for hit in range(0, DRAW_SIZE + 1)}
    return {
        "draws_tested": draws_count,
        "combination_count": len(clean_combinations),
        "average_best_hits": round(total_best_hits / draws_count, 6) if draws_count else 0.0,
        "average_total_row_hits": round(total_all_row_hits / draws_count, 6) if draws_count else 0.0,
        "max_best_hits": int(best_seen),
        "empty_draws": int(counts.get(0, 0)),
        "empty_rate_percent": round((counts.get(0, 0) / draws_count * 100.0) if draws_count else 0.0, 6),
        "at_least_1_percent": round(_hit_distribution_percent(counts, draws_count, 1), 6),
        "at_least_2_percent": round(_hit_distribution_percent(counts, draws_count, 2), 6),
        "at_least_3_percent": round(_hit_distribution_percent(counts, draws_count, 3), 6),
        "at_least_4_percent": round(_hit_distribution_percent(counts, draws_count, 4), 6),
        "at_least_5_percent": round(_hit_distribution_percent(counts, draws_count, 5), 6),
        "exact_6_count": int(counts.get(6, 0)),
        "exact_6_percent": round((counts.get(6, 0) / draws_count * 100.0) if draws_count else 0.0, 9),
        "distribution": distribution,
    }


def _historical_score(metrics: dict[str, Any], cost_eur: float) -> float:
    return round(
        float(metrics.get("average_best_hits", 0.0)) * 28.0
        + float(metrics.get("at_least_2_percent", 0.0)) * 0.08
        + float(metrics.get("at_least_3_percent", 0.0)) * 0.55
        + float(metrics.get("at_least_4_percent", 0.0)) * 1.40
        + float(metrics.get("at_least_5_percent", 0.0)) * 4.00
        + float(metrics.get("exact_6_percent", 0.0)) * 7.00
        - max(0.0, float(cost_eur)) * 0.10,
        3,
    )


def _efficiency_score(metrics: dict[str, Any], combination_count: int, cost_eur: float) -> float:
    base = _historical_score(metrics, cost_eur)
    divisor = math.sqrt(max(1, int(combination_count)))
    return round(base / divisor, 3)


def _random_package(combination_count: int, rng: random.Random) -> list[list[int]]:
    target = max(1, int(combination_count))
    combinations: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    attempts = 0
    while len(combinations) < target and attempts < target * 100:
        attempts += 1
        combo = sorted(rng.sample(range(1, TOTAL_NUMBERS + 1), DRAW_SIZE))
        key = tuple(combo)
        if key not in seen:
            seen.add(key)
            combinations.append(combo)
    return combinations


def build_random_baselines(draws: list[dict[str, Any]], counts: list[int], trials: int = DEFAULT_RANDOM_TRIALS) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for combination_count in sorted(set(max(1, int(count)) for count in counts)):
        avg_values: list[float] = []
        empty_values: list[float] = []
        pct3_values: list[float] = []
        pct4_values: list[float] = []
        max_values: list[int] = []
        for trial in range(max(1, int(trials))):
            rng = random.Random(9200 + combination_count * 100 + trial)
            metrics = evaluate_package(_random_package(combination_count, rng), draws)
            avg_values.append(float(metrics["average_best_hits"]))
            empty_values.append(float(metrics["empty_rate_percent"]))
            pct3_values.append(float(metrics["at_least_3_percent"]))
            pct4_values.append(float(metrics["at_least_4_percent"]))
            max_values.append(int(metrics["max_best_hits"]))
        result[combination_count] = {
            "combination_count": combination_count,
            "trials": max(1, int(trials)),
            "random_average_best_hits": round(statistics.mean(avg_values), 6),
            "random_empty_rate_percent": round(statistics.mean(empty_values), 6),
            "random_at_least_3_percent": round(statistics.mean(pct3_values), 6),
            "random_at_least_4_percent": round(statistics.mean(pct4_values), 6),
            "random_max_best_hits_avg": round(statistics.mean(max_values), 3),
        }
    return result


def evaluate_strategy_option(option: dict[str, Any], draws: list[dict[str, Any]], baseline: dict[str, Any] | None) -> dict[str, Any]:
    combinations = _option_combinations(option)
    metrics = evaluate_package(combinations, draws)
    cost = float(option.get("cost_eur_at_090") or option.get("cost_eur") or 0.0)
    combination_count = len(combinations)
    historical_score = _historical_score(metrics, cost)
    efficiency_score = _efficiency_score(metrics, combination_count, cost)
    baseline_avg = float((baseline or {}).get("random_average_best_hits", 0.0))
    baseline_empty = float((baseline or {}).get("random_empty_rate_percent", 0.0))

    return {
        "option_id": str(option.get("option_id", "")),
        "strategy_label": _strategy_label(option),
        "strategy_type": _strategy_type(option),
        "mode_label": str(option.get("mode_label", "-")),
        "source_label": str(option.get("source_label", "-")),
        "core_numbers": _numbers_text([int(n) for n in option.get("core_numbers", []) if _parse_int(n) is not None]),
        "combination_count": combination_count,
        "unique_covered_numbers": int(option.get("unique_covered_numbers") or len({n for combo in combinations for n in combo})),
        "cost_eur_at_090": round(cost, 2),
        "system_score_step91": float(option.get("system_score", 0.0)),
        "draws_tested": int(metrics["draws_tested"]),
        "average_best_hits": metrics["average_best_hits"],
        "average_total_row_hits": metrics["average_total_row_hits"],
        "max_best_hits": metrics["max_best_hits"],
        "empty_rate_percent": metrics["empty_rate_percent"],
        "at_least_1_percent": metrics["at_least_1_percent"],
        "at_least_2_percent": metrics["at_least_2_percent"],
        "at_least_3_percent": metrics["at_least_3_percent"],
        "at_least_4_percent": metrics["at_least_4_percent"],
        "at_least_5_percent": metrics["at_least_5_percent"],
        "exact_6_count": metrics["exact_6_count"],
        "exact_6_percent": metrics["exact_6_percent"],
        "historical_score": historical_score,
        "budget_efficiency_score": efficiency_score,
        "random_average_best_hits": round(baseline_avg, 6),
        "average_hits_vs_random": round(float(metrics["average_best_hits"]) - baseline_avg, 6),
        "random_empty_rate_percent": round(baseline_empty, 6),
        "empty_rate_vs_random": round(float(metrics["empty_rate_percent"]) - baseline_empty, 6),
        "distribution": metrics["distribution"],
    }


def build_system_strategy_backtest_center(random_trials: int = DEFAULT_RANDOM_TRIALS) -> dict[str, Any]:
    step91 = _load_step91_model()
    draws = load_historical_draws()
    options = [option for option in step91.get("options", []) if _option_combinations(option)]
    combination_counts = [len(_option_combinations(option)) for option in options]
    baselines = build_random_baselines(draws, combination_counts, trials=random_trials) if draws else {}

    strategy_rows = [
        evaluate_strategy_option(option, draws, baselines.get(len(_option_combinations(option))))
        for option in options
    ]
    strategy_rows.sort(key=lambda row: (-float(row["budget_efficiency_score"]), float(row["cost_eur_at_090"]), -float(row["historical_score"])))

    practical_rows = [row for row in strategy_rows if row["cost_eur_at_090"] <= 10.0]
    four_combo_rows = [row for row in strategy_rows if row["combination_count"] == 4]
    best_overall = max(strategy_rows, key=lambda row: float(row["historical_score"]), default={})
    best_efficiency = max(strategy_rows, key=lambda row: float(row["budget_efficiency_score"]), default={})
    best_under_10 = max(practical_rows, key=lambda row: float(row["budget_efficiency_score"]), default=best_efficiency)
    best_four_combo = max(four_combo_rows, key=lambda row: float(row["budget_efficiency_score"]), default=best_under_10)

    distribution_rows: list[dict[str, Any]] = []
    for row in strategy_rows:
        for hit_bucket in range(0, DRAW_SIZE + 1):
            count = int(row["distribution"].get(str(hit_bucket), 0))
            percent = count / int(row["draws_tested"]) * 100.0 if int(row["draws_tested"]) else 0.0
            distribution_rows.append(
                {
                    "strategy_label": row["strategy_label"],
                    "combination_count": row["combination_count"],
                    "best_hit_bucket": hit_bucket,
                    "draw_count": count,
                    "draw_percent": round(percent, 6),
                }
            )

    baseline_rows = [baselines[key] for key in sorted(baselines)]
    latest_draw = draws[-1] if draws else {}

    return {
        "step": 92,
        "status": "OK" if strategy_rows and draws else "NO_DATA",
        "title_bg": "Тест на системни стратегии",
        "safe_note_bg": SAFE_NOTE_BG,
        "method_summary_bg": (
            "Слоят сравнява готовите Step 91 стратегии върху историческите тиражи. "
            "За всяка стратегия се отчита най-доброто съвпадение в рамките на нейния пакет от комбинации, "
            "празен риск, 2+/3+/4+/5+ съвпадения и сравнение с детерминиран случаен baseline със същия брой комбинации."
        ),
        "draws_tested": len(draws),
        "latest_draw_id": latest_draw.get("draw_id", ""),
        "latest_draw_date": latest_draw.get("date", ""),
        "latest_draw_numbers": latest_draw.get("numbers", []),
        "strategies_tested": len(strategy_rows),
        "random_trials_per_combination_count": random_trials,
        "best_overall_by_historical_score": best_overall,
        "best_by_budget_efficiency": best_efficiency,
        "best_under_10_eur": best_under_10,
        "best_four_combo_strategy": best_four_combo,
        "strategy_rows": strategy_rows,
        "distribution_rows": distribution_rows,
        "random_baseline_rows": baseline_rows,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def save_system_strategy_backtest_outputs(model: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    best_under_10 = model.get("best_under_10_eur", {}) or {}
    best_four = model.get("best_four_combo_strategy", {}) or {}
    summary = {
        "step": model.get("step"),
        "status": model.get("status"),
        "title_bg": model.get("title_bg"),
        "draws_tested": model.get("draws_tested", 0),
        "strategies_tested": model.get("strategies_tested", 0),
        "random_trials_per_combination_count": model.get("random_trials_per_combination_count", 0),
        "best_under_10_eur": best_under_10.get("strategy_label", ""),
        "best_under_10_budget_efficiency_score": best_under_10.get("budget_efficiency_score", 0.0),
        "best_under_10_average_best_hits": best_under_10.get("average_best_hits", 0.0),
        "best_four_combo_strategy": best_four.get("strategy_label", ""),
        "best_four_combo_budget_efficiency_score": best_four.get("budget_efficiency_score", 0.0),
        "safe_note_bg": model.get("safe_note_bg", SAFE_NOTE_BG),
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    result_fields = [
        "option_id",
        "strategy_label",
        "strategy_type",
        "mode_label",
        "source_label",
        "core_numbers",
        "combination_count",
        "unique_covered_numbers",
        "cost_eur_at_090",
        "system_score_step91",
        "draws_tested",
        "average_best_hits",
        "average_total_row_hits",
        "max_best_hits",
        "empty_rate_percent",
        "at_least_1_percent",
        "at_least_2_percent",
        "at_least_3_percent",
        "at_least_4_percent",
        "at_least_5_percent",
        "exact_6_count",
        "exact_6_percent",
        "historical_score",
        "budget_efficiency_score",
        "random_average_best_hits",
        "average_hits_vs_random",
        "random_empty_rate_percent",
        "empty_rate_vs_random",
    ]
    _write_csv(RESULTS_CSV_PATH, model.get("strategy_rows", []), result_fields)

    distribution_fields = ["strategy_label", "combination_count", "best_hit_bucket", "draw_count", "draw_percent"]
    _write_csv(DISTRIBUTION_CSV_PATH, model.get("distribution_rows", []), distribution_fields)

    baseline_fields = [
        "combination_count",
        "trials",
        "random_average_best_hits",
        "random_empty_rate_percent",
        "random_at_least_3_percent",
        "random_at_least_4_percent",
        "random_max_best_hits_avg",
    ]
    _write_csv(BASELINE_CSV_PATH, model.get("random_baseline_rows", []), baseline_fields)

    lines = [
        f"# {model.get('title_bg', 'Тест на системни стратегии')}",
        "",
        f"- Статус: **{model.get('status', '-')}**",
        f"- Исторически тиражи в теста: **{model.get('draws_tested', 0)}**",
        f"- Сравнени стратегии: **{model.get('strategies_tested', 0)}**",
        f"- Случайни baseline опити на брой комбинации: **{model.get('random_trials_per_combination_count', 0)}**",
        "",
        "## Най-добра практична стратегия до 10 EUR",
        f"- **{best_under_10.get('strategy_label', '-')}**",
        f"- Комбинации: **{best_under_10.get('combination_count', 0)}**",
        f"- Цена при 0.90 EUR: **{float(best_under_10.get('cost_eur_at_090', 0.0)):.2f} EUR**",
        f"- Средно най-добро съвпадение: **{float(best_under_10.get('average_best_hits', 0.0)):.4f}**",
        f"- Празни тиражи: **{float(best_under_10.get('empty_rate_percent', 0.0)):.4f}%**",
        f"- 3+ съвпадения: **{float(best_under_10.get('at_least_3_percent', 0.0)):.4f}%**",
        f"- Бюджетна ефективност: **{float(best_under_10.get('budget_efficiency_score', 0.0)):.3f}**",
        "",
        "## Най-добра стратегия с 4 комбинации",
        f"- **{best_four.get('strategy_label', '-')}**",
        f"- Средно най-добро съвпадение: **{float(best_four.get('average_best_hits', 0.0)):.4f}**",
        f"- Празни тиражи: **{float(best_four.get('empty_rate_percent', 0.0)):.4f}%**",
        "",
        str(model.get("safe_note_bg", SAFE_NOTE_BG)),
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    model = build_system_strategy_backtest_center()
    save_system_strategy_backtest_outputs(model)
    return model
