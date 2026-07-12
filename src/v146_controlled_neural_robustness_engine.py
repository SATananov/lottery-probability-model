from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from src.v144_reproducible_experiment_registry_engine import (
    DATASET_PATH,
    REGISTRY_PATH,
    canonical_hash,
    dataset_descriptor,
    environment_descriptor,
    load_draws,
    sha256_file,
)
from src.v145_experimental_neural_dynamics_engine import (
    DRAW_SIZE,
    TOTAL_NUMBERS,
    _aggregate_trial,
    _binary_draw,
    _build_reservoir,
    _package_metrics,
    _score_package,
    _uniform_random_package,
    _update_state,
    _write_csv,
    _write_registry_index,
    _upsert_registry,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "models" / "v146_controlled_neural_robustness_policy.json"
STATUS_PATH = ROOT / "models" / "v146_controlled_neural_robustness_status.json"
RUN_RESULTS_CSV_PATH = ROOT / "reports" / "v146_neural_robustness_run_results.csv"
SEED_STABILITY_CSV_PATH = ROOT / "reports" / "v146_neural_robustness_seed_stability.csv"
FOLD_STABILITY_CSV_PATH = ROOT / "reports" / "v146_neural_robustness_fold_stability.csv"
DRAW_COMPARISON_CSV_PATH = ROOT / "reports" / "v146_neural_robustness_draw_comparison.csv"
SUMMARY_JSON_PATH = ROOT / "reports" / "v146_neural_robustness_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v146_neural_robustness_summary.md"
EXPERIMENT_DIR = ROOT / "reports" / "experiments" / "v146"

BASELINE_KEYS = (
    "frequency_walk_forward",
    "recency_weighted_walk_forward",
    "recent_window_frequency",
    "frequency_recency_blend",
    "uniform_random_mean",
)

DEFAULT_CONFIG: dict[str, Any] = {
    "fold_size": 120,
    "fold_count": 3,
    "minimum_training_draws": 500,
    "seeds": [1462026, 1462027, 1462028, 1462029, 1462030],
    "package_size": 12,
    "random_trials_per_run": 10,
    "frequency_pool_size": 49,
    "recency_decay": 0.985,
    "recent_window_draws": 104,
    "blend_frequency_weight": 0.5,
    "reservoir_size": 32,
    "leak_rate": 0.28,
    "spectral_radius": 0.82,
    "input_scale": 0.65,
    "bias_scale": 0.05,
    "ridge_alpha": 12.0,
    "score_power": 1.4,
    "bootstrap_iterations": 5000,
    "confidence_level": 0.95,
    "minimum_seed_positive_rate": 0.80,
    "minimum_fold_positive_rate": 1.00,
    "maximum_sign_test_p_value": 0.05,
    "maximum_neural_seed_spread": 0.20,
}

SAFE_NOTE_BG = (
    "Step 146 е изолиран robustness експеримент върху исторически тиражи. Той не е свързан с production "
    "pipeline, не създава реални фишове и не доказва предвидимост на бъдещи случайни тиражи."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _draw_key(draw: dict[str, Any]) -> str:
    return f"{draw.get('year')}-{draw.get('draw_number')}"


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=np.float64)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    if maximum - minimum <= 1e-12:
        return np.ones_like(values)
    return (values - minimum) / (maximum - minimum)


def _validate_config(config: dict[str, Any]) -> None:
    if int(config["fold_size"]) < 60:
        raise ValueError("fold_size must be at least 60")
    if not 2 <= int(config["fold_count"]) <= 8:
        raise ValueError("fold_count must be between 2 and 8")
    if int(config["minimum_training_draws"]) < 100:
        raise ValueError("minimum_training_draws must be at least 100")
    seeds = [int(value) for value in config.get("seeds", [])]
    if len(seeds) < 3 or len(seeds) != len(set(seeds)):
        raise ValueError("At least three unique seeds are required")
    if not 1 <= int(config["package_size"]) <= 100:
        raise ValueError("package_size must be between 1 and 100")
    if not 3 <= int(config["random_trials_per_run"]) <= 200:
        raise ValueError("random_trials_per_run must be between 3 and 200")
    if not DRAW_SIZE <= int(config["frequency_pool_size"]) <= TOTAL_NUMBERS:
        raise ValueError("frequency_pool_size must be between 6 and 49")
    if not 0.0 < float(config["recency_decay"]) < 1.0:
        raise ValueError("recency_decay must be between 0 and 1")
    if not 12 <= int(config["recent_window_draws"]) <= 1000:
        raise ValueError("recent_window_draws must be between 12 and 1000")
    if not 0.0 <= float(config["blend_frequency_weight"]) <= 1.0:
        raise ValueError("blend_frequency_weight must be between 0 and 1")
    if not 4 <= int(config["reservoir_size"]) <= 256:
        raise ValueError("reservoir_size must be between 4 and 256")
    if not 0.0 < float(config["leak_rate"]) <= 1.0:
        raise ValueError("leak_rate must be between 0 and 1")
    if not 0.0 < float(config["spectral_radius"]) < 1.5:
        raise ValueError("spectral_radius must be between 0 and 1.5")
    if float(config["ridge_alpha"]) <= 0.0:
        raise ValueError("ridge_alpha must be positive")
    if float(config["score_power"]) <= 0.0:
        raise ValueError("score_power must be positive")
    if int(config["bootstrap_iterations"]) < 1000:
        raise ValueError("bootstrap_iterations must be at least 1000")
    if not 0.80 <= float(config["confidence_level"]) < 1.0:
        raise ValueError("confidence_level must be between 0.80 and 1.0")


def _exact_two_sided_sign_test(wins: int, losses: int) -> float:
    effective = int(wins) + int(losses)
    if effective <= 0:
        return 1.0
    smaller = min(int(wins), int(losses))
    cumulative = sum(math.comb(effective, index) for index in range(smaller + 1)) / (2.0 ** effective)
    return min(1.0, 2.0 * cumulative)


def _bootstrap_mean_ci(
    values: list[float],
    *,
    confidence_level: float,
    iterations: int,
    seed: int,
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (float(values[0]), float(values[0]))
    rng = random.Random(int(seed))
    size = len(values)
    means: list[float] = []
    for _ in range(int(iterations)):
        sample = [values[rng.randrange(size)] for _ in range(size)]
        means.append(statistics.fmean(sample))
    means.sort()
    alpha = (1.0 - float(confidence_level)) / 2.0
    low_index = max(0, min(len(means) - 1, int(math.floor(alpha * (len(means) - 1)))))
    high_index = max(0, min(len(means) - 1, int(math.ceil((1.0 - alpha) * (len(means) - 1)))))
    return (float(means[low_index]), float(means[high_index]))


def _fold_boundaries(draw_count: int, config: dict[str, Any]) -> list[dict[str, int]]:
    fold_size = int(config["fold_size"])
    fold_count = int(config["fold_count"])
    minimum_training = int(config["minimum_training_draws"])
    required = minimum_training + fold_size * fold_count
    if draw_count < required:
        raise ValueError(f"Not enough draws for robustness design: {draw_count} < {required}")
    start_of_block = draw_count - fold_size * fold_count
    folds: list[dict[str, int]] = []
    for index in range(fold_count):
        start = start_of_block + index * fold_size
        end = start + fold_size
        folds.append({"fold": index + 1, "start": start, "end": end})
    return folds


def _evaluate_seed_fold(
    draws: list[dict[str, Any]],
    *,
    fold: dict[str, int],
    seed: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    start = int(fold["start"])
    end = int(fold["end"])
    training_draws = draws[:start]
    holdout = draws[start:end]
    run_config = dict(config)
    run_config["seed"] = int(seed)

    parameters = _build_reservoir(run_config)
    reservoir_size = int(config["reservoir_size"])
    feature_size = reservoir_size + 1
    leak_rate = float(config["leak_rate"])
    ridge_alpha = float(config["ridge_alpha"])
    state = np.zeros(reservoir_size, dtype=np.float64)
    state = _update_state(state, training_draws[0]["numbers"], parameters, leak_rate)
    gram = np.zeros((feature_size, feature_size), dtype=np.float64)
    targets = np.zeros((feature_size, TOTAL_NUMBERS), dtype=np.float64)

    for index in range(1, len(training_draws)):
        feature = np.concatenate(([1.0], state))
        target = _binary_draw(training_draws[index]["numbers"])
        gram += np.outer(feature, feature)
        targets += np.outer(feature, target)
        state = _update_state(state, training_draws[index]["numbers"], parameters, leak_rate)

    frequency_scores = np.zeros(TOTAL_NUMBERS, dtype=np.float64)
    recency_scores = np.zeros(TOTAL_NUMBERS, dtype=np.float64)
    recency_decay = float(config["recency_decay"])
    recent_window = int(config["recent_window_draws"])
    recent_queue: deque[np.ndarray] = deque(maxlen=recent_window)
    recent_scores = np.zeros(TOTAL_NUMBERS, dtype=np.float64)
    for draw in training_draws:
        binary = _binary_draw(draw["numbers"])
        frequency_scores += binary
        recency_scores = recency_decay * recency_scores + binary
        if len(recent_queue) == recent_queue.maxlen:
            recent_scores -= recent_queue[0]
        recent_queue.append(binary)
        recent_scores += binary

    series: dict[str, dict[str, list[int]]] = {
        key: {"best": [], "total": []}
        for key in (
            "neural_dynamics_reservoir",
            "frequency_walk_forward",
            "recency_weighted_walk_forward",
            "recent_window_frequency",
            "frequency_recency_blend",
        )
    }
    random_best: list[list[int]] = [[] for _ in range(int(config["random_trials_per_run"]))]
    random_total: list[list[int]] = [[] for _ in range(int(config["random_trials_per_run"]))]
    draw_rows: list[dict[str, Any]] = []
    state_norms: list[float] = []
    score_stds: list[float] = []
    identity = np.eye(feature_size, dtype=np.float64)
    identity[0, 0] = 0.0

    blend_weight = float(config["blend_frequency_weight"])
    fold_number = int(fold["fold"])
    for offset, draw in enumerate(holdout):
        absolute_index = start + offset
        feature = np.concatenate(([1.0], state))
        coefficients = np.linalg.solve(gram + ridge_alpha * identity, targets)
        raw_scores = feature @ coefficients
        neural_scores = 1.0 / (1.0 + np.exp(-np.clip(raw_scores, -40.0, 40.0)))
        blend_scores = (
            blend_weight * _normalize_scores(frequency_scores)
            + (1.0 - blend_weight) * _normalize_scores(recency_scores)
        )
        score_map = {
            "neural_dynamics_reservoir": neural_scores,
            "frequency_walk_forward": frequency_scores,
            "recency_weighted_walk_forward": recency_scores,
            "recent_window_frequency": recent_scores,
            "frequency_recency_blend": blend_scores,
        }
        state_norms.append(float(np.linalg.norm(state)))
        score_stds.append(float(np.std(neural_scores)))

        metrics: dict[str, tuple[int, int]] = {}
        for strategy_index, (strategy, scores) in enumerate(score_map.items(), start=1):
            package = _score_package(
                scores,
                int(config["package_size"]),
                int(seed) + fold_number * 100_000_000 + strategy_index * 10_000_000 + absolute_index,
                float(config["score_power"]),
                int(config["frequency_pool_size"]),
            )
            best, total = _package_metrics(package, draw["numbers"])
            series[strategy]["best"].append(best)
            series[strategy]["total"].append(total)
            metrics[strategy] = (best, total)

        random_draw_best: list[int] = []
        for trial in range(int(config["random_trials_per_run"])):
            package = _uniform_random_package(
                int(config["package_size"]),
                int(seed) + fold_number * 100_000_000 + 90_000_000 + trial * 1_000_003 + absolute_index,
            )
            best, total = _package_metrics(package, draw["numbers"])
            random_best[trial].append(best)
            random_total[trial].append(total)
            random_draw_best.append(best)

        draw_rows.append(
            {
                "seed": int(seed),
                "fold": fold_number,
                "draw_event_id": draw.get("draw_event_id"),
                "draw_key": _draw_key(draw),
                "date": draw.get("date", ""),
                "neural_best_hits": metrics["neural_dynamics_reservoir"][0],
                "frequency_best_hits": metrics["frequency_walk_forward"][0],
                "recency_best_hits": metrics["recency_weighted_walk_forward"][0],
                "recent_window_best_hits": metrics["recent_window_frequency"][0],
                "blend_best_hits": metrics["frequency_recency_blend"][0],
                "uniform_random_mean_best_hits": round(statistics.fmean(random_draw_best), 9),
            }
        )

        target = _binary_draw(draw["numbers"])
        gram += np.outer(feature, feature)
        targets += np.outer(feature, target)
        state = _update_state(state, draw["numbers"], parameters, leak_rate)
        frequency_scores += target
        recency_scores = recency_decay * recency_scores + target
        if len(recent_queue) == recent_queue.maxlen:
            recent_scores -= recent_queue[0]
        recent_queue.append(target)
        recent_scores += target

    aggregates = {
        strategy: _aggregate_trial(strategy, 0, values["best"], values["total"])
        for strategy, values in series.items()
    }
    random_trials = [
        _aggregate_trial("uniform_random", trial + 1, random_best[trial], random_total[trial])
        for trial in range(int(config["random_trials_per_run"]))
    ]
    random_averages = [float(row["average_best_hits"]) for row in random_trials]
    random_mean = statistics.fmean(random_averages)
    unit_values = {
        "neural_dynamics_reservoir": float(aggregates["neural_dynamics_reservoir"]["average_best_hits"]),
        "frequency_walk_forward": float(aggregates["frequency_walk_forward"]["average_best_hits"]),
        "recency_weighted_walk_forward": float(aggregates["recency_weighted_walk_forward"]["average_best_hits"]),
        "recent_window_frequency": float(aggregates["recent_window_frequency"]["average_best_hits"]),
        "frequency_recency_blend": float(aggregates["frequency_recency_blend"]["average_best_hits"]),
        "uniform_random_mean": float(random_mean),
    }
    return {
        "seed": int(seed),
        "fold": fold_number,
        "training_draws_initial": len(training_draws),
        "holdout_draws": len(holdout),
        "holdout_first_draw": _draw_key(holdout[0]),
        "holdout_last_draw": _draw_key(holdout[-1]),
        "aggregates": aggregates,
        "random_trials": random_trials,
        "random_summary": {
            "trials": len(random_trials),
            "average_best_hits_mean": round(random_mean, 9),
            "average_best_hits_std": round(statistics.pstdev(random_averages), 9),
            "average_best_hits_min": round(min(random_averages), 9),
            "average_best_hits_max": round(max(random_averages), 9),
        },
        "unit_values": unit_values,
        "diagnostics": {
            "actual_spectral_radius": round(parameters.actual_spectral_radius, 9),
            "state_norm_mean": round(statistics.fmean(state_norms), 9),
            "state_norm_max": round(max(state_norms), 9),
            "score_standard_deviation_mean": round(statistics.fmean(score_stds), 9),
            "all_states_finite": True,
        },
        "draw_rows": draw_rows,
    }


def _comparison_summary(runs: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    neural_values = [float(run["unit_values"]["neural_dynamics_reservoir"]) for run in runs]
    for baseline_index, baseline in enumerate(BASELINE_KEYS, start=1):
        differences = [
            float(run["unit_values"]["neural_dynamics_reservoir"]) - float(run["unit_values"][baseline])
            for run in runs
        ]
        lower, upper = _bootstrap_mean_ci(
            differences,
            confidence_level=float(config["confidence_level"]),
            iterations=int(config["bootstrap_iterations"]),
            seed=1469000 + baseline_index,
        )
        wins = sum(value > 0 for value in differences)
        ties = sum(value == 0 for value in differences)
        losses = sum(value < 0 for value in differences)
        seed_means: dict[int, list[float]] = {}
        fold_means: dict[int, list[float]] = {}
        for run, difference in zip(runs, differences):
            seed_means.setdefault(int(run["seed"]), []).append(difference)
            fold_means.setdefault(int(run["fold"]), []).append(difference)
        seed_advantages = {key: statistics.fmean(values) for key, values in seed_means.items()}
        fold_advantages = {key: statistics.fmean(values) for key, values in fold_means.items()}
        comparisons[baseline] = {
            "baseline": baseline,
            "units": len(differences),
            "mean_advantage": round(statistics.fmean(differences), 9),
            "confidence_level": float(config["confidence_level"]),
            "bootstrap_ci_lower": round(lower, 9),
            "bootstrap_ci_upper": round(upper, 9),
            "wins": wins,
            "ties": ties,
            "losses": losses,
            "two_sided_sign_test_p_value": round(_exact_two_sided_sign_test(wins, losses), 9),
            "positive_seed_rate": round(sum(value > 0 for value in seed_advantages.values()) / len(seed_advantages), 9),
            "positive_fold_rate": round(sum(value > 0 for value in fold_advantages.values()) / len(fold_advantages), 9),
            "seed_advantages": {str(key): round(value, 9) for key, value in sorted(seed_advantages.items())},
            "fold_advantages": {str(key): round(value, 9) for key, value in sorted(fold_advantages.items())},
        }

    neural_seed_means: dict[int, list[float]] = {}
    neural_fold_means: dict[int, list[float]] = {}
    for run, value in zip(runs, neural_values):
        neural_seed_means.setdefault(int(run["seed"]), []).append(value)
        neural_fold_means.setdefault(int(run["fold"]), []).append(value)
    per_seed = {key: statistics.fmean(values) for key, values in neural_seed_means.items()}
    per_fold = {key: statistics.fmean(values) for key, values in neural_fold_means.items()}
    seed_spread = max(per_seed.values()) - min(per_seed.values())

    requirements = {
        "all_mean_advantages_positive": all(value["mean_advantage"] > 0 for value in comparisons.values()),
        "all_confidence_intervals_above_zero": all(value["bootstrap_ci_lower"] > 0 for value in comparisons.values()),
        "all_sign_tests_significant": all(
            value["two_sided_sign_test_p_value"] <= float(config["maximum_sign_test_p_value"])
            for value in comparisons.values()
        ),
        "all_seed_positive_rates_sufficient": all(
            value["positive_seed_rate"] >= float(config["minimum_seed_positive_rate"])
            for value in comparisons.values()
        ),
        "all_fold_positive_rates_sufficient": all(
            value["positive_fold_rate"] >= float(config["minimum_fold_positive_rate"])
            for value in comparisons.values()
        ),
        "neural_seed_spread_within_limit": seed_spread <= float(config["maximum_neural_seed_spread"]),
        "minimum_design_size_met": len(neural_seed_means) >= 5 and len(neural_fold_means) >= 3,
    }
    passed = all(requirements.values())
    return {
        "baselines": comparisons,
        "stability": {
            "neural_run_mean": round(statistics.fmean(neural_values), 9),
            "neural_run_std": round(statistics.pstdev(neural_values), 9),
            "neural_run_min": round(min(neural_values), 9),
            "neural_run_max": round(max(neural_values), 9),
            "neural_seed_spread": round(seed_spread, 9),
            "neural_seed_means": {str(key): round(value, 9) for key, value in sorted(per_seed.items())},
            "neural_fold_means": {str(key): round(value, 9) for key, value in sorted(per_fold.items())},
        },
        "promotion_requirements": requirements,
        "promotion_gate_passed": bool(passed),
        "interpretation": (
            "The neural robustness experiment passed every exploratory stability gate. Automatic production promotion remains disabled; independent confirmation would still be required."
            if passed
            else "The neural robustness experiment did not pass every multi-seed, multi-period confidence and stability gate. The model remains research-only and isolated from ticket generation."
        ),
    }


def evaluate_controlled_neural_robustness(draws: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    _validate_config(config)
    folds = _fold_boundaries(len(draws), config)
    runs: list[dict[str, Any]] = []
    for fold in folds:
        for seed in [int(value) for value in config["seeds"]]:
            runs.append(_evaluate_seed_fold(draws, fold=fold, seed=seed, config=config))

    comparison = _comparison_summary(runs, config)
    strategy_values: dict[str, list[float]] = {
        "neural_dynamics_reservoir": [],
        **{key: [] for key in BASELINE_KEYS},
    }
    for run in runs:
        for strategy in strategy_values:
            strategy_values[strategy].append(float(run["unit_values"][strategy]))
    strategy_summary = {
        strategy: {
            "strategy": strategy,
            "runs": len(values),
            "average_best_hits_mean": round(statistics.fmean(values), 9),
            "average_best_hits_std": round(statistics.pstdev(values), 9),
            "average_best_hits_min": round(min(values), 9),
            "average_best_hits_max": round(max(values), 9),
        }
        for strategy, values in strategy_values.items()
    }
    return {
        "split_policy": {
            "policy": "expanding_window_walk_forward",
            "robustness_design": "three_non_overlapping_historical_folds_multi_seed",
            "fold_count": len(folds),
            "fold_size": int(config["fold_size"]),
            "holdout_draws": len(folds) * int(config["fold_size"]),
            "seed_count": len(config["seeds"]),
            "run_count": len(runs),
            "target_draw_added_after_scoring": True,
            "data_leakage_guard": "Each target draw is scored before it is added to the expanding training state.",
            "folds": [
                {
                    "fold": int(fold["fold"]),
                    "training_draws_initial": int(fold["start"]),
                    "holdout_draws": int(fold["end"] - fold["start"]),
                    "holdout_first_draw": _draw_key(draws[int(fold["start"])]),
                    "holdout_last_draw": _draw_key(draws[int(fold["end"]) - 1]),
                }
                for fold in folds
            ],
        },
        "architecture": {
            "name": "multi_seed_continuous_time_inspired_leaky_reservoir_with_online_ridge_readout",
            "state_equation": "h_t=(1-leak)h_(t-1)+leak*tanh(W_in*x_t+W_rec*h_(t-1)+b)",
            "readout": "walk_forward_ridge_regression",
            "reservoir_size": int(config["reservoir_size"]),
            "seed_count": len(config["seeds"]),
            "hardware_claim": "none",
            "ode_solver_claim": "none",
            "production_integration": False,
        },
        "strategy_summary": strategy_summary,
        "comparison": comparison,
        "runs": runs,
        "diagnostics": {
            "all_states_finite": all(run["diagnostics"]["all_states_finite"] for run in runs),
            "spectral_radius_min": min(run["diagnostics"]["actual_spectral_radius"] for run in runs),
            "spectral_radius_max": max(run["diagnostics"]["actual_spectral_radius"] for run in runs),
            "run_count": len(runs),
        },
    }


def code_descriptor() -> dict[str, Any]:
    relative_paths = [
        "src/v146_controlled_neural_robustness_engine.py",
        "tools/run_controlled_neural_robustness.py",
    ]
    rows = [
        {"path": relative, "sha256": sha256_file(ROOT / relative)}
        for relative in relative_paths
        if (ROOT / relative).exists()
    ]
    return {"files": rows, "combined_sha256": canonical_hash(rows)}


def _policy(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "step": 146,
        "name": "Controlled Neural Experiment Expansion & Robustness Validation",
        "project_context": "Personal experimental statistics and software-engineering project",
        "default_configuration": config,
        "robustness_scope": {
            "multi_seed": True,
            "non_overlapping_historical_folds": True,
            "bootstrap_confidence_intervals": True,
            "paired_sign_tests": True,
            "additional_simple_baselines": ["recent_window_frequency", "frequency_recency_blend"],
        },
        "promotion_gate": {
            "all_mean_advantages_positive": True,
            "all_bootstrap_ci_lower_bounds_above_zero": True,
            "maximum_sign_test_p_value": float(config["maximum_sign_test_p_value"]),
            "minimum_seed_positive_rate": float(config["minimum_seed_positive_rate"]),
            "minimum_fold_positive_rate": float(config["minimum_fold_positive_rate"]),
            "maximum_neural_seed_spread": float(config["maximum_neural_seed_spread"]),
            "automatic_promotion": False,
        },
        "guardrails": {
            "future_data_leakage": "forbidden",
            "heavy_ml_retraining": "not_performed",
            "personal_journal_access": "not_used",
            "production_pipeline_access": "forbidden",
            "real_ticket_generation": "forbidden",
            "results_claim": "historical_robustness_experiment_only",
        },
        "safe_note_bg": SAFE_NOTE_BG,
    }


def _write_outputs(report: dict[str, Any], registry_rows: list[dict[str, Any]]) -> None:
    experiment = report["experiment"]
    results = experiment["results"]
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(json.dumps(report["policy"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = {
        "step": 146,
        "status": "completed",
        "experiment_id": experiment["experiment_id"],
        "registry_entries": len(registry_rows),
        "dataset_sha256": experiment["dataset"]["sha256"],
        "configuration_sha256": experiment["reproducibility"]["configuration_sha256"],
        "result_signature_sha256": experiment["reproducibility"]["result_signature_sha256"],
        "fold_count": results["split_policy"]["fold_count"],
        "seed_count": results["split_policy"]["seed_count"],
        "run_count": results["split_policy"]["run_count"],
        "promotion_gate_passed": bool(results["comparison"]["promotion_gate_passed"]),
        "production_integration_enabled": False,
        "real_ticket_generation_enabled": False,
        "heavy_ml_retraining_performed": False,
        "personal_journal_used": False,
        "future_data_leakage_detected": False,
        "safe_note_bg": SAFE_NOTE_BG,
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_rows: list[dict[str, Any]] = []
    seed_rows: dict[int, list[dict[str, Any]]] = {}
    fold_rows: dict[int, list[dict[str, Any]]] = {}
    draw_rows: list[dict[str, Any]] = []
    for run in results["runs"]:
        row = {
            "seed": run["seed"],
            "fold": run["fold"],
            "training_draws_initial": run["training_draws_initial"],
            "holdout_draws": run["holdout_draws"],
            "holdout_first_draw": run["holdout_first_draw"],
            "holdout_last_draw": run["holdout_last_draw"],
            **run["unit_values"],
        }
        for baseline in BASELINE_KEYS:
            row[f"neural_minus_{baseline}"] = round(
                float(run["unit_values"]["neural_dynamics_reservoir"]) - float(run["unit_values"][baseline]), 9
            )
        run_rows.append(row)
        seed_rows.setdefault(int(run["seed"]), []).append(row)
        fold_rows.setdefault(int(run["fold"]), []).append(row)
        draw_rows.extend(run["draw_rows"])

    fields = [
        "seed", "fold", "training_draws_initial", "holdout_draws", "holdout_first_draw", "holdout_last_draw",
        "neural_dynamics_reservoir", *BASELINE_KEYS,
        *[f"neural_minus_{key}" for key in BASELINE_KEYS],
    ]
    _write_csv(RUN_RESULTS_CSV_PATH, run_rows, fields)

    def stability_rows(groups: dict[int, list[dict[str, Any]]], key_name: str) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for key, rows in sorted(groups.items()):
            item: dict[str, Any] = {key_name: key, "runs": len(rows)}
            for strategy in ("neural_dynamics_reservoir", *BASELINE_KEYS):
                item[strategy] = round(statistics.fmean(float(row[strategy]) for row in rows), 9)
            for baseline in BASELINE_KEYS:
                item[f"neural_minus_{baseline}"] = round(
                    float(item["neural_dynamics_reservoir"]) - float(item[baseline]), 9
                )
            output.append(item)
        return output

    stability_fields = [
        "runs", "neural_dynamics_reservoir", *BASELINE_KEYS,
        *[f"neural_minus_{key}" for key in BASELINE_KEYS],
    ]
    _write_csv(SEED_STABILITY_CSV_PATH, stability_rows(seed_rows, "seed"), ["seed", *stability_fields])
    _write_csv(FOLD_STABILITY_CSV_PATH, stability_rows(fold_rows, "fold"), ["fold", *stability_fields])
    _write_csv(
        DRAW_COMPARISON_CSV_PATH,
        draw_rows,
        [
            "seed", "fold", "draw_event_id", "draw_key", "date", "neural_best_hits",
            "frequency_best_hits", "recency_best_hits", "recent_window_best_hits", "blend_best_hits",
            "uniform_random_mean_best_hits",
        ],
    )
    _write_registry_index(registry_rows)

    summary = {
        "step": 146,
        "status": "completed",
        "experiment_id": experiment["experiment_id"],
        "dataset": experiment["dataset"],
        "configuration": experiment["configuration"],
        "split_policy": results["split_policy"],
        "architecture": results["architecture"],
        "strategy_summary": results["strategy_summary"],
        "comparison": results["comparison"],
        "diagnostics": results["diagnostics"],
        "reproducibility": experiment["reproducibility"],
        "registry_entries": len(registry_rows),
        "safe_note_bg": SAFE_NOTE_BG,
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    (EXPERIMENT_DIR / f"{experiment['experiment_id']}.json").write_text(
        json.dumps(experiment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    strategy = results["strategy_summary"]
    comparison = results["comparison"]
    lines = [
        "# Step 146 — Controlled Neural Experiment Expansion & Robustness Validation",
        "",
        f"- Experiment ID: `{experiment['experiment_id']}`",
        f"- Dataset SHA-256: `{experiment['dataset']['sha256']}`",
        f"- Latest draw: **{experiment['dataset']['latest_draw']}**",
        f"- Historical folds: **{results['split_policy']['fold_count']} × {results['split_policy']['fold_size']} draws**",
        f"- Random seeds: **{results['split_policy']['seed_count']}**",
        f"- Robustness runs: **{results['split_policy']['run_count']}**",
        f"- Promotion gate: **{'PASS' if comparison['promotion_gate_passed'] else 'BLOCKED'}**",
        "",
        "## Aggregate average best hits",
        "",
        "| Strategy | Mean | Std | Min | Max |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("neural_dynamics_reservoir", *BASELINE_KEYS):
        row = strategy[key]
        lines.append(
            f"| {key} | {row['average_best_hits_mean']:.6f} | {row['average_best_hits_std']:.6f} | "
            f"{row['average_best_hits_min']:.6f} | {row['average_best_hits_max']:.6f} |"
        )
    lines.extend([
        "",
        "## Confidence and stability comparison",
        "",
        "| Baseline | Mean advantage | 95% CI | Sign p | Positive seeds | Positive folds |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for key in BASELINE_KEYS:
        row = comparison["baselines"][key]
        lines.append(
            f"| {key} | {row['mean_advantage']:.6f} | [{row['bootstrap_ci_lower']:.6f}, {row['bootstrap_ci_upper']:.6f}] | "
            f"{row['two_sided_sign_test_p_value']:.6f} | {row['positive_seed_rate']:.1%} | {row['positive_fold_rate']:.1%} |"
        )
    lines.extend([
        "",
        "## Promotion requirements",
        "",
        *[f"- {key}: **{'PASS' if value else 'FAIL'}**" for key, value in comparison["promotion_requirements"].items()],
        "",
        "## Conclusion",
        "",
        comparison["interpretation"],
        "",
        SAFE_NOTE_BG,
        "",
    ])
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_controlled_neural_robustness(
    *,
    config: dict[str, Any] | None = None,
    write_outputs: bool = True,
    register: bool = True,
) -> dict[str, Any]:
    resolved = json.loads(json.dumps(DEFAULT_CONFIG if config is None else config))
    resolved["seeds"] = [int(value) for value in resolved["seeds"]]
    _validate_config(resolved)
    draws = load_draws()
    dataset = dataset_descriptor(draws)
    code = code_descriptor()
    results = evaluate_controlled_neural_robustness(draws, resolved)
    deterministic_result = {
        "dataset_sha256": dataset["sha256"],
        "configuration": resolved,
        "split_policy": results["split_policy"],
        "architecture": results["architecture"],
        "strategy_summary": results["strategy_summary"],
        "comparison": results["comparison"],
        "diagnostics": results["diagnostics"],
        "runs": results["runs"],
    }
    config_hash = canonical_hash(resolved)
    result_signature = canonical_hash(deterministic_result)
    experiment_id = f"EXP-146-{dataset['sha256'][:10]}-{config_hash[:10]}"
    now = utc_now()
    experiment = {
        "experiment_id": experiment_id,
        "step": 146,
        "title": "Controlled multi-seed, multi-period neural robustness validation",
        "status": "completed",
        "experiment_type": "research_only_neural_robustness_validation",
        "created_at_utc": now,
        "last_run_at_utc": now,
        "dataset": dataset,
        "code": code,
        "environment": environment_descriptor(),
        "configuration": resolved,
        "random_seed": resolved["seeds"],
        "split_policy": results["split_policy"],
        "results": results,
        "artifacts": [
            REGISTRY_PATH.relative_to(ROOT).as_posix(),
            STATUS_PATH.relative_to(ROOT).as_posix(),
            RUN_RESULTS_CSV_PATH.relative_to(ROOT).as_posix(),
            SEED_STABILITY_CSV_PATH.relative_to(ROOT).as_posix(),
            FOLD_STABILITY_CSV_PATH.relative_to(ROOT).as_posix(),
            DRAW_COMPARISON_CSV_PATH.relative_to(ROOT).as_posix(),
            SUMMARY_JSON_PATH.relative_to(ROOT).as_posix(),
            SUMMARY_MD_PATH.relative_to(ROOT).as_posix(),
            (EXPERIMENT_DIR / f"{experiment_id}.json").relative_to(ROOT).as_posix(),
        ],
        "reproducibility": {
            "command": "python tools/run_controlled_neural_robustness.py",
            "configuration_sha256": config_hash,
            "dataset_sha256": dataset["sha256"],
            "code_sha256": code["combined_sha256"],
            "result_signature_sha256": result_signature,
            "deterministic_for_same_dataset_code_config": True,
        },
        "conclusion": results["comparison"]["interpretation"],
        "safe_note_bg": SAFE_NOTE_BG,
        "heavy_ml_retraining_performed": False,
        "personal_journal_used": False,
        "future_data_leakage_detected": False,
        "production_pipeline_used": False,
        "real_ticket_generation_performed": False,
    }
    policy = _policy(resolved)
    registry_rows: list[dict[str, Any]] = []
    if REGISTRY_PATH.exists():
        registry_rows = [
            json.loads(line)
            for line in REGISTRY_PATH.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
    if write_outputs and register:
        registry_rows = _upsert_registry(experiment)
    elif register:
        registry_rows = [row for row in registry_rows if row.get("experiment_id") != experiment_id] + [experiment]
    report = {"policy": policy, "experiment": experiment, "registry_entries": len(registry_rows)}
    if write_outputs:
        _write_outputs(report, registry_rows)
    return report


def deterministic_signature(report: dict[str, Any]) -> str:
    return str(((report.get("experiment") or {}).get("reproducibility") or {}).get("result_signature_sha256") or "")
