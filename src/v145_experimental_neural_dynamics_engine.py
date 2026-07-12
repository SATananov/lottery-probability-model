from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from src.v144_reproducible_experiment_registry_engine import (
    DATASET_PATH,
    INDEX_CSV_PATH,
    REGISTRY_PATH,
    canonical_hash,
    dataset_descriptor,
    dataset_sha256,
    environment_descriptor,
    load_draws,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "models" / "v145_experimental_neural_dynamics_policy.json"
STATUS_PATH = ROOT / "models" / "v145_experimental_neural_dynamics_status.json"
RESULTS_CSV_PATH = ROOT / "reports" / "v145_neural_dynamics_results.csv"
DRAW_COMPARISON_CSV_PATH = ROOT / "reports" / "v145_neural_dynamics_draw_comparison.csv"
SUMMARY_JSON_PATH = ROOT / "reports" / "v145_neural_dynamics_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v145_neural_dynamics_summary.md"
EXPERIMENT_DIR = ROOT / "reports" / "experiments" / "v145"

TOTAL_NUMBERS = 49
DRAW_SIZE = 6

DEFAULT_CONFIG: dict[str, Any] = {
    "holdout_draws": 240,
    "minimum_training_draws": 500,
    "package_size": 12,
    "random_trials": 50,
    "frequency_pool_size": 49,
    "recency_decay": 0.985,
    "reservoir_size": 32,
    "leak_rate": 0.28,
    "spectral_radius": 0.82,
    "input_scale": 0.65,
    "bias_scale": 0.05,
    "ridge_alpha": 12.0,
    "score_power": 1.4,
    "seed": 1452026,
}

SAFE_NOTE_BG = (
    "Това е изолиран исторически sandbox експеримент. Neural-dynamics моделът не е включен в production "
    "pipeline, не създава реални фишове и не доказва предвидимост на бъдещи случайни тиражи."
)


@dataclass(frozen=True)
class ReservoirParameters:
    input_weights: np.ndarray
    recurrent_weights: np.ndarray
    bias: np.ndarray
    actual_spectral_radius: float


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _draw_key(draw: dict[str, Any]) -> str:
    return f"{draw.get('year')}-{draw.get('draw_number')}"


def _binary_draw(numbers: Iterable[int]) -> np.ndarray:
    vector = np.zeros(TOTAL_NUMBERS, dtype=np.float64)
    indexes = [int(number) - 1 for number in numbers]
    vector[indexes] = 1.0
    return vector


def _centered_draw(numbers: Iterable[int]) -> np.ndarray:
    vector = np.full(TOTAL_NUMBERS, -DRAW_SIZE / TOTAL_NUMBERS, dtype=np.float64)
    indexes = [int(number) - 1 for number in numbers]
    vector[indexes] = 1.0 - DRAW_SIZE / TOTAL_NUMBERS
    return vector


def _build_reservoir(config: dict[str, Any]) -> ReservoirParameters:
    rng = np.random.default_rng(int(config["seed"]))
    size = int(config["reservoir_size"])
    input_weights = rng.normal(0.0, 1.0 / math.sqrt(TOTAL_NUMBERS), (size, TOTAL_NUMBERS))
    input_weights *= float(config["input_scale"])
    recurrent = rng.normal(0.0, 1.0 / math.sqrt(size), (size, size))
    eigenvalues = np.linalg.eigvals(recurrent)
    current_radius = float(np.max(np.abs(eigenvalues))) if eigenvalues.size else 1.0
    if not math.isfinite(current_radius) or current_radius <= 0.0:
        raise ValueError("Unable to initialize a stable recurrent matrix")
    recurrent *= float(config["spectral_radius"]) / current_radius
    scaled_eigenvalues = np.linalg.eigvals(recurrent)
    actual_radius = float(np.max(np.abs(scaled_eigenvalues))) if scaled_eigenvalues.size else 0.0
    bias = rng.normal(0.0, float(config["bias_scale"]), size)
    return ReservoirParameters(input_weights, recurrent, bias, actual_radius)


def _update_state(
    state: np.ndarray,
    numbers: Iterable[int],
    parameters: ReservoirParameters,
    leak_rate: float,
) -> np.ndarray:
    signal = (
        parameters.input_weights @ _centered_draw(numbers)
        + parameters.recurrent_weights @ state
        + parameters.bias
    )
    next_state = (1.0 - leak_rate) * state + leak_rate * np.tanh(signal)
    if not np.all(np.isfinite(next_state)):
        raise ValueError("Neural dynamics state became non-finite")
    return next_state


def _weighted_sample_without_replacement(
    values: list[int],
    weights: list[float],
    count: int,
    rng: random.Random,
) -> list[int]:
    available = list(values)
    available_weights = [max(0.0, float(value)) for value in weights]
    selected: list[int] = []
    for _ in range(min(count, len(available))):
        total = sum(available_weights)
        if total <= 0.0:
            index = rng.randrange(len(available))
        else:
            target = rng.random() * total
            cumulative = 0.0
            index = len(available) - 1
            for candidate_index, weight in enumerate(available_weights):
                cumulative += weight
                if target <= cumulative:
                    index = candidate_index
                    break
        selected.append(available.pop(index))
        available_weights.pop(index)
    return sorted(selected)


def _score_package(
    scores: np.ndarray,
    package_size: int,
    seed: int,
    score_power: float,
    pool_size: int,
) -> list[list[int]]:
    clean_scores = np.asarray(scores, dtype=np.float64)
    clean_scores = np.nan_to_num(clean_scores, nan=0.0, posinf=0.0, neginf=0.0)
    ranked_indexes = sorted(range(TOTAL_NUMBERS), key=lambda index: (-float(clean_scores[index]), index))
    active_indexes = ranked_indexes[: max(DRAW_SIZE, min(TOTAL_NUMBERS, int(pool_size)))]
    active_values = [index + 1 for index in active_indexes]
    active_raw = [float(clean_scores[index]) for index in active_indexes]
    minimum = min(active_raw, default=0.0)
    weights = [max(value - minimum + 1e-9, 1e-9) ** float(score_power) for value in active_raw]

    rng = random.Random(int(seed))
    package: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    attempts = 0
    while len(package) < int(package_size) and attempts < int(package_size) * 500:
        attempts += 1
        combo = tuple(_weighted_sample_without_replacement(active_values, weights, DRAW_SIZE, rng))
        if len(combo) == DRAW_SIZE and combo not in seen:
            seen.add(combo)
            package.append(list(combo))

    if len(package) < int(package_size):
        all_values = list(range(1, TOTAL_NUMBERS + 1))
        fallback_weights = [max(float(clean_scores[index]) - float(np.min(clean_scores)) + 1e-9, 1e-9) for index in range(TOTAL_NUMBERS)]
        while len(package) < int(package_size) and attempts < int(package_size) * 1500:
            attempts += 1
            combo = tuple(_weighted_sample_without_replacement(all_values, fallback_weights, DRAW_SIZE, rng))
            if len(combo) == DRAW_SIZE and combo not in seen:
                seen.add(combo)
                package.append(list(combo))
    if len(package) != int(package_size):
        raise RuntimeError("Unable to build the requested number of unique combinations")
    return package


def _uniform_random_package(package_size: int, seed: int) -> list[list[int]]:
    rng = random.Random(int(seed))
    package: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    while len(package) < int(package_size):
        combo = tuple(sorted(rng.sample(range(1, TOTAL_NUMBERS + 1), DRAW_SIZE)))
        if combo not in seen:
            seen.add(combo)
            package.append(list(combo))
    return package


def _package_metrics(package: list[list[int]], actual_numbers: Iterable[int]) -> tuple[int, int]:
    actual = {int(number) for number in actual_numbers}
    hits = [len(actual.intersection(combo)) for combo in package]
    return (max(hits, default=0), sum(hits))


def _aggregate_trial(strategy: str, trial: int, best_hits: list[int], total_hits: list[int]) -> dict[str, Any]:
    draws = len(best_hits)
    return {
        "strategy": strategy,
        "trial": int(trial),
        "draws_tested": draws,
        "average_best_hits": round(statistics.fmean(best_hits), 9) if best_hits else 0.0,
        "average_total_hits": round(statistics.fmean(total_hits), 9) if total_hits else 0.0,
        "max_best_hits": max(best_hits, default=0),
        "at_least_2_percent": round(sum(hit >= 2 for hit in best_hits) / draws * 100.0, 9) if draws else 0.0,
        "at_least_3_percent": round(sum(hit >= 3 for hit in best_hits) / draws * 100.0, 9) if draws else 0.0,
        "at_least_4_percent": round(sum(hit >= 4 for hit in best_hits) / draws * 100.0, 9) if draws else 0.0,
        "at_least_5_percent": round(sum(hit >= 5 for hit in best_hits) / draws * 100.0, 9) if draws else 0.0,
        "exact_6_count": sum(hit == 6 for hit in best_hits),
        "distribution": {str(hit): best_hits.count(hit) for hit in range(DRAW_SIZE + 1)},
    }


def _exact_two_sided_sign_test(wins: int, losses: int) -> float:
    effective = int(wins) + int(losses)
    if effective <= 0:
        return 1.0
    smaller = min(int(wins), int(losses))
    cumulative = sum(math.comb(effective, index) for index in range(smaller + 1)) / (2.0 ** effective)
    return min(1.0, 2.0 * cumulative)


def _paired_comparison(candidate: list[int], baseline: list[int], baseline_name: str) -> dict[str, Any]:
    if len(candidate) != len(baseline):
        raise ValueError("Paired comparison series must have equal length")
    differences = [int(left) - int(right) for left, right in zip(candidate, baseline)]
    wins = sum(value > 0 for value in differences)
    ties = sum(value == 0 for value in differences)
    losses = sum(value < 0 for value in differences)
    return {
        "baseline": baseline_name,
        "draws": len(differences),
        "mean_best_hits_difference": round(statistics.fmean(differences), 9) if differences else 0.0,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "two_sided_sign_test_p_value": round(_exact_two_sided_sign_test(wins, losses), 9),
    }


def _validate_config(config: dict[str, Any]) -> None:
    if int(config["holdout_draws"]) < 30:
        raise ValueError("holdout_draws must be at least 30")
    if int(config["minimum_training_draws"]) < 100:
        raise ValueError("minimum_training_draws must be at least 100")
    if not 1 <= int(config["package_size"]) <= 100:
        raise ValueError("package_size must be between 1 and 100")
    if not 1 <= int(config["random_trials"]) <= 1000:
        raise ValueError("random_trials must be between 1 and 1000")
    if not DRAW_SIZE <= int(config["frequency_pool_size"]) <= TOTAL_NUMBERS:
        raise ValueError("frequency_pool_size must be between 6 and 49")
    if not 0.0 < float(config["recency_decay"]) < 1.0:
        raise ValueError("recency_decay must be between 0 and 1")
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


def evaluate_neural_dynamics_sandbox(draws: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    _validate_config(config)
    holdout_draws = min(int(config["holdout_draws"]), len(draws) - int(config["minimum_training_draws"]))
    if holdout_draws <= 0:
        raise ValueError("Not enough draws for the requested training/holdout split")
    split_index = len(draws) - holdout_draws
    training_draws = draws[:split_index]
    holdout = draws[split_index:]

    parameters = _build_reservoir(config)
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
    for draw in training_draws:
        binary = _binary_draw(draw["numbers"])
        frequency_scores += binary
        recency_scores = recency_decay * recency_scores + binary

    neural_best: list[int] = []
    neural_total: list[int] = []
    frequency_best: list[int] = []
    frequency_total: list[int] = []
    recency_best: list[int] = []
    recency_total: list[int] = []
    random_best: list[list[int]] = [[] for _ in range(int(config["random_trials"]))]
    random_total: list[list[int]] = [[] for _ in range(int(config["random_trials"]))]
    draw_rows: list[dict[str, Any]] = []
    state_norms: list[float] = []
    score_standard_deviations: list[float] = []

    identity = np.eye(feature_size, dtype=np.float64)
    identity[0, 0] = 0.0

    for offset, draw in enumerate(holdout):
        absolute_index = split_index + offset
        feature = np.concatenate(([1.0], state))
        coefficients = np.linalg.solve(gram + ridge_alpha * identity, targets)
        raw_scores = feature @ coefficients
        neural_scores = 1.0 / (1.0 + np.exp(-np.clip(raw_scores, -40.0, 40.0)))
        state_norms.append(float(np.linalg.norm(state)))
        score_standard_deviations.append(float(np.std(neural_scores)))

        neural_package = _score_package(
            neural_scores,
            int(config["package_size"]),
            int(config["seed"]) + 1_000_000 + absolute_index,
            float(config["score_power"]),
            int(config["frequency_pool_size"]),
        )
        frequency_package = _score_package(
            frequency_scores,
            int(config["package_size"]),
            int(config["seed"]) + 2_000_000 + absolute_index,
            float(config["score_power"]),
            int(config["frequency_pool_size"]),
        )
        recency_package = _score_package(
            recency_scores,
            int(config["package_size"]),
            int(config["seed"]) + 3_000_000 + absolute_index,
            float(config["score_power"]),
            int(config["frequency_pool_size"]),
        )

        neural_metrics = _package_metrics(neural_package, draw["numbers"])
        frequency_metrics = _package_metrics(frequency_package, draw["numbers"])
        recency_metrics = _package_metrics(recency_package, draw["numbers"])
        neural_best.append(neural_metrics[0])
        neural_total.append(neural_metrics[1])
        frequency_best.append(frequency_metrics[0])
        frequency_total.append(frequency_metrics[1])
        recency_best.append(recency_metrics[0])
        recency_total.append(recency_metrics[1])

        random_draw_best: list[int] = []
        for trial in range(int(config["random_trials"])):
            package = _uniform_random_package(
                int(config["package_size"]),
                int(config["seed"]) + trial * 1_000_003 + absolute_index,
            )
            best, total = _package_metrics(package, draw["numbers"])
            random_best[trial].append(best)
            random_total[trial].append(total)
            random_draw_best.append(best)

        draw_rows.append(
            {
                "draw_event_id": draw.get("draw_event_id"),
                "draw_key": _draw_key(draw),
                "date": draw.get("date", ""),
                "neural_best_hits": neural_metrics[0],
                "frequency_best_hits": frequency_metrics[0],
                "recency_best_hits": recency_metrics[0],
                "uniform_random_mean_best_hits": round(statistics.fmean(random_draw_best), 9),
                "neural_minus_frequency": neural_metrics[0] - frequency_metrics[0],
                "neural_minus_recency": neural_metrics[0] - recency_metrics[0],
            }
        )

        # Strict walk-forward rule: score first, learn from the target second.
        target = _binary_draw(draw["numbers"])
        gram += np.outer(feature, feature)
        targets += np.outer(feature, target)
        state = _update_state(state, draw["numbers"], parameters, leak_rate)
        frequency_scores += target
        recency_scores = recency_decay * recency_scores + target

    neural_result = _aggregate_trial("neural_dynamics_reservoir", 0, neural_best, neural_total)
    frequency_result = _aggregate_trial("frequency_walk_forward", 0, frequency_best, frequency_total)
    recency_result = _aggregate_trial("recency_weighted_walk_forward", 0, recency_best, recency_total)
    random_results = [
        _aggregate_trial("uniform_random", trial + 1, random_best[trial], random_total[trial])
        for trial in range(int(config["random_trials"]))
    ]
    random_averages = [float(row["average_best_hits"]) for row in random_results]
    neural_average = float(neural_result["average_best_hits"])
    random_mean = statistics.fmean(random_averages) if random_averages else 0.0
    random_percentile = (
        sum(value <= neural_average for value in random_averages) / len(random_averages) * 100.0
        if random_averages
        else 0.0
    )
    empirical_p = (
        (1 + sum(value >= neural_average for value in random_averages)) / (len(random_averages) + 1)
        if random_averages
        else 1.0
    )

    paired = {
        "versus_frequency": _paired_comparison(neural_best, frequency_best, "frequency_walk_forward"),
        "versus_recency": _paired_comparison(neural_best, recency_best, "recency_weighted_walk_forward"),
    }
    comparison = {
        "neural_minus_frequency_average_best_hits": round(
            neural_average - float(frequency_result["average_best_hits"]), 9
        ),
        "neural_minus_recency_average_best_hits": round(
            neural_average - float(recency_result["average_best_hits"]), 9
        ),
        "neural_minus_random_mean_average_best_hits": round(neural_average - random_mean, 9),
        "neural_percentile_among_random_trials": round(random_percentile, 3),
        "empirical_one_sided_p_value_vs_random_trials": round(empirical_p, 9),
        "paired": paired,
    }
    beats_all = (
        comparison["neural_minus_frequency_average_best_hits"] > 0
        and comparison["neural_minus_recency_average_best_hits"] > 0
        and comparison["neural_minus_random_mean_average_best_hits"] > 0
        and empirical_p <= 0.05
    )
    comparison["promotion_gate_passed"] = bool(beats_all)
    comparison["interpretation"] = (
        "The neural-dynamics sandbox passed the exploratory comparison gate on this historical holdout. "
        "This still does not establish future predictive power and does not authorize production use."
        if beats_all
        else "The neural-dynamics sandbox did not pass the promotion gate on this historical holdout. "
        "It remains research-only and is not connected to ticket generation."
    )

    return {
        "split": {
            "policy": "expanding_window_walk_forward",
            "training_draws_initial": len(training_draws),
            "holdout_draws": len(holdout),
            "holdout_first_draw": _draw_key(holdout[0]),
            "holdout_last_draw": _draw_key(holdout[-1]),
            "target_draw_added_after_scoring": True,
            "data_leakage_guard": (
                "At each holdout point, the neural readout, frequency scores and recency scores use only strictly earlier draws."
            ),
        },
        "architecture": {
            "name": "continuous_time_inspired_leaky_reservoir_with_online_ridge_readout",
            "state_equation": "h_t=(1-leak)h_(t-1)+leak*tanh(W_in*x_t+W_rec*h_(t-1)+b)",
            "readout": "walk_forward_ridge_regression",
            "reservoir_size": reservoir_size,
            "requested_spectral_radius": float(config["spectral_radius"]),
            "actual_spectral_radius": round(parameters.actual_spectral_radius, 9),
            "hardware_claim": "none",
            "ode_solver_claim": "none",
            "production_integration": False,
        },
        "neural_dynamics": neural_result,
        "frequency_baseline": frequency_result,
        "recency_baseline": recency_result,
        "random_trials": random_results,
        "random_summary": {
            "trials": len(random_results),
            "average_best_hits_mean": round(random_mean, 9),
            "average_best_hits_std": round(statistics.pstdev(random_averages), 9) if random_averages else 0.0,
            "average_best_hits_min": round(min(random_averages), 9) if random_averages else 0.0,
            "average_best_hits_max": round(max(random_averages), 9) if random_averages else 0.0,
        },
        "comparison": comparison,
        "diagnostics": {
            "state_norm_mean": round(statistics.fmean(state_norms), 9) if state_norms else 0.0,
            "state_norm_max": round(max(state_norms), 9) if state_norms else 0.0,
            "score_standard_deviation_mean": round(statistics.fmean(score_standard_deviations), 9)
            if score_standard_deviations
            else 0.0,
            "all_states_finite": True,
        },
        "draw_rows": draw_rows,
    }


def code_descriptor() -> dict[str, Any]:
    relative_paths = [
        "src/v145_experimental_neural_dynamics_engine.py",
        "tools/run_experimental_neural_dynamics.py",
    ]
    rows = []
    for relative in relative_paths:
        path = ROOT / relative
        if path.exists():
            rows.append({"path": relative, "sha256": sha256_file(path)})
    return {"files": rows, "combined_sha256": canonical_hash(rows)}


def _read_registry() -> list[dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(REGISTRY_PATH.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Registry line {line_number} is not a JSON object")
        rows.append(payload)
    return rows


def _write_registry(rows: list[dict[str, Any]]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda row: str(row.get("experiment_id", "")))
    REGISTRY_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered),
        encoding="utf-8",
    )


def _upsert_registry(entry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = _read_registry()
    previous = next((row for row in rows if row.get("experiment_id") == entry.get("experiment_id")), None)
    if previous and previous.get("created_at_utc"):
        entry["created_at_utc"] = previous["created_at_utc"]
    rows = [row for row in rows if row.get("experiment_id") != entry.get("experiment_id")]
    rows.append(entry)
    _write_registry(rows)
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_registry_index(rows: list[dict[str, Any]]) -> None:
    index_rows = [
        {
            "experiment_id": row.get("experiment_id"),
            "status": row.get("status"),
            "title": row.get("title"),
            "created_at_utc": row.get("created_at_utc"),
            "last_run_at_utc": row.get("last_run_at_utc"),
            "dataset_sha256": (row.get("dataset") or {}).get("sha256"),
            "latest_draw": (row.get("dataset") or {}).get("latest_draw"),
            "seed": row.get("random_seed"),
            "holdout_draws": (row.get("split_policy") or {}).get("holdout_draws"),
            "result_signature_sha256": (row.get("reproducibility") or {}).get("result_signature_sha256"),
        }
        for row in sorted(rows, key=lambda item: str(item.get("experiment_id", "")))
    ]
    _write_csv(
        INDEX_CSV_PATH,
        index_rows,
        [
            "experiment_id",
            "status",
            "title",
            "created_at_utc",
            "last_run_at_utc",
            "dataset_sha256",
            "latest_draw",
            "seed",
            "holdout_draws",
            "result_signature_sha256",
        ],
    )


def _policy(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "step": 145,
        "name": "Experimental Neural Dynamics Sandbox and Baseline Comparison",
        "project_context": "Personal experimental statistics and software-engineering project",
        "default_configuration": config,
        "architecture_scope": {
            "implemented": "continuous-time-inspired leaky reservoir with online ridge readout",
            "not_implemented": [
                "analogue neural hardware",
                "in-memory computing hardware",
                "adaptive ODE solver",
                "production ticket integration",
            ],
        },
        "promotion_gate": {
            "must_beat_frequency": True,
            "must_beat_recency": True,
            "must_beat_random_mean": True,
            "maximum_empirical_p_value_vs_random": 0.05,
            "automatic_promotion": False,
        },
        "guardrails": {
            "future_data_leakage": "forbidden",
            "heavy_ml_retraining": "not_performed",
            "personal_journal_access": "not_used",
            "production_pipeline_access": "forbidden",
            "real_ticket_generation": "forbidden",
            "results_claim": "historical_experiment_only",
        },
        "safe_note_bg": SAFE_NOTE_BG,
    }


def _write_outputs(report: dict[str, Any], registry_rows: list[dict[str, Any]]) -> None:
    experiment = report["experiment"]
    results = experiment["results"]
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(json.dumps(report["policy"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = {
        "step": 145,
        "status": "completed",
        "experiment_id": experiment["experiment_id"],
        "registry_entries": len(registry_rows),
        "dataset_sha256": experiment["dataset"]["sha256"],
        "configuration_sha256": experiment["reproducibility"]["configuration_sha256"],
        "result_signature_sha256": experiment["reproducibility"]["result_signature_sha256"],
        "holdout_draws": experiment["split_policy"]["holdout_draws"],
        "promotion_gate_passed": bool(results["comparison"]["promotion_gate_passed"]),
        "production_integration_enabled": False,
        "real_ticket_generation_enabled": False,
        "heavy_ml_retraining_performed": False,
        "personal_journal_used": False,
        "future_data_leakage_detected": False,
        "safe_note_bg": SAFE_NOTE_BG,
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result_rows = [
        results["neural_dynamics"],
        results["frequency_baseline"],
        results["recency_baseline"],
        *results["random_trials"],
    ]
    _write_csv(
        RESULTS_CSV_PATH,
        [{key: value for key, value in row.items() if key != "distribution"} for row in result_rows],
        [
            "strategy",
            "trial",
            "draws_tested",
            "average_best_hits",
            "average_total_hits",
            "max_best_hits",
            "at_least_2_percent",
            "at_least_3_percent",
            "at_least_4_percent",
            "at_least_5_percent",
            "exact_6_count",
        ],
    )
    _write_csv(
        DRAW_COMPARISON_CSV_PATH,
        results["draw_rows"],
        [
            "draw_event_id",
            "draw_key",
            "date",
            "neural_best_hits",
            "frequency_best_hits",
            "recency_best_hits",
            "uniform_random_mean_best_hits",
            "neural_minus_frequency",
            "neural_minus_recency",
        ],
    )
    _write_registry_index(registry_rows)

    summary = {
        "step": 145,
        "status": "completed",
        "experiment_id": experiment["experiment_id"],
        "dataset": experiment["dataset"],
        "configuration": experiment["configuration"],
        "split_policy": experiment["split_policy"],
        "architecture": results["architecture"],
        "neural_dynamics": results["neural_dynamics"],
        "frequency_baseline": results["frequency_baseline"],
        "recency_baseline": results["recency_baseline"],
        "random_summary": results["random_summary"],
        "comparison": results["comparison"],
        "diagnostics": results["diagnostics"],
        "reproducibility": experiment["reproducibility"],
        "registry_entries": len(registry_rows),
        "safe_note_bg": SAFE_NOTE_BG,
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    (EXPERIMENT_DIR / f"{experiment['experiment_id']}.json").write_text(
        json.dumps(experiment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    neural = results["neural_dynamics"]
    frequency = results["frequency_baseline"]
    recency = results["recency_baseline"]
    random_summary = results["random_summary"]
    comparison = results["comparison"]
    lines = [
        "# Step 145 — Experimental Neural Dynamics Sandbox",
        "",
        f"- Experiment ID: `{experiment['experiment_id']}`",
        f"- Dataset SHA-256: `{experiment['dataset']['sha256']}`",
        f"- Latest draw: **{experiment['dataset']['latest_draw']}**",
        f"- Initial training draws: **{experiment['split_policy']['training_draws_initial']}**",
        f"- Holdout draws: **{experiment['split_policy']['holdout_draws']}**",
        f"- Package size: **{experiment['configuration']['package_size']}** combinations",
        f"- Random trials: **{experiment['configuration']['random_trials']}**",
        f"- Seed: **{experiment['random_seed']}**",
        "",
        "## Architecture",
        "",
        f"- Model: `{results['architecture']['name']}`",
        f"- State equation: `{results['architecture']['state_equation']}`",
        f"- Reservoir size: **{results['architecture']['reservoir_size']}**",
        f"- Actual spectral radius: **{results['architecture']['actual_spectral_radius']}**",
        "- Production integration: **No**",
        "",
        "## Historical holdout results",
        "",
        f"- Neural dynamics average best hits: **{neural['average_best_hits']:.6f}**",
        f"- Frequency baseline average best hits: **{frequency['average_best_hits']:.6f}**",
        f"- Recency baseline average best hits: **{recency['average_best_hits']:.6f}**",
        f"- Uniform-random mean average best hits: **{random_summary['average_best_hits_mean']:.6f}**",
        f"- Neural minus frequency: **{comparison['neural_minus_frequency_average_best_hits']:.6f}**",
        f"- Neural minus recency: **{comparison['neural_minus_recency_average_best_hits']:.6f}**",
        f"- Neural minus random mean: **{comparison['neural_minus_random_mean_average_best_hits']:.6f}**",
        f"- Empirical p-value versus random trials: **{comparison['empirical_one_sided_p_value_vs_random_trials']:.6f}**",
        f"- Promotion gate passed: **{'Yes' if comparison['promotion_gate_passed'] else 'No'}**",
        "",
        "## Reproducibility",
        "",
        f"- Configuration hash: `{experiment['reproducibility']['configuration_sha256']}`",
        f"- Code hash: `{experiment['code']['combined_sha256']}`",
        f"- Result signature: `{experiment['reproducibility']['result_signature_sha256']}`",
        f"- Command: `{experiment['reproducibility']['command']}`",
        "",
        "## Conclusion",
        "",
        experiment["conclusion"],
        "",
        SAFE_NOTE_BG,
        "",
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_experimental_neural_dynamics(
    *,
    holdout_draws: int = int(DEFAULT_CONFIG["holdout_draws"]),
    minimum_training_draws: int = int(DEFAULT_CONFIG["minimum_training_draws"]),
    package_size: int = int(DEFAULT_CONFIG["package_size"]),
    random_trials: int = int(DEFAULT_CONFIG["random_trials"]),
    frequency_pool_size: int = int(DEFAULT_CONFIG["frequency_pool_size"]),
    recency_decay: float = float(DEFAULT_CONFIG["recency_decay"]),
    reservoir_size: int = int(DEFAULT_CONFIG["reservoir_size"]),
    leak_rate: float = float(DEFAULT_CONFIG["leak_rate"]),
    spectral_radius: float = float(DEFAULT_CONFIG["spectral_radius"]),
    input_scale: float = float(DEFAULT_CONFIG["input_scale"]),
    bias_scale: float = float(DEFAULT_CONFIG["bias_scale"]),
    ridge_alpha: float = float(DEFAULT_CONFIG["ridge_alpha"]),
    score_power: float = float(DEFAULT_CONFIG["score_power"]),
    seed: int = int(DEFAULT_CONFIG["seed"]),
    write_outputs: bool = True,
    register: bool = True,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "holdout_draws": int(holdout_draws),
        "minimum_training_draws": int(minimum_training_draws),
        "package_size": int(package_size),
        "random_trials": int(random_trials),
        "frequency_pool_size": int(frequency_pool_size),
        "recency_decay": float(recency_decay),
        "reservoir_size": int(reservoir_size),
        "leak_rate": float(leak_rate),
        "spectral_radius": float(spectral_radius),
        "input_scale": float(input_scale),
        "bias_scale": float(bias_scale),
        "ridge_alpha": float(ridge_alpha),
        "score_power": float(score_power),
        "seed": int(seed),
    }
    _validate_config(config)
    draws = load_draws()
    dataset = dataset_descriptor(draws)
    code = code_descriptor()
    results = evaluate_neural_dynamics_sandbox(draws, config)
    deterministic_result = {
        "dataset_sha256": dataset["sha256"],
        "configuration": config,
        "split": results["split"],
        "architecture": results["architecture"],
        "neural_dynamics": results["neural_dynamics"],
        "frequency_baseline": results["frequency_baseline"],
        "recency_baseline": results["recency_baseline"],
        "random_summary": results["random_summary"],
        "random_trials": results["random_trials"],
        "comparison": results["comparison"],
        "diagnostics": results["diagnostics"],
        "draw_rows": results["draw_rows"],
    }
    config_hash = canonical_hash(config)
    result_signature = canonical_hash(deterministic_result)
    experiment_id = f"EXP-145-{dataset['sha256'][:10]}-{config_hash[:10]}"
    now = utc_now()
    experiment = {
        "experiment_id": experiment_id,
        "step": 145,
        "title": "Neural dynamics sandbox versus frequency, recency and uniform-random baselines",
        "status": "completed",
        "experiment_type": "research_only_neural_dynamics_sandbox",
        "created_at_utc": now,
        "last_run_at_utc": now,
        "dataset": dataset,
        "code": code,
        "environment": environment_descriptor(),
        "configuration": config,
        "random_seed": config["seed"],
        "split_policy": results["split"],
        "results": results,
        "artifacts": [
            REGISTRY_PATH.relative_to(ROOT).as_posix(),
            STATUS_PATH.relative_to(ROOT).as_posix(),
            RESULTS_CSV_PATH.relative_to(ROOT).as_posix(),
            DRAW_COMPARISON_CSV_PATH.relative_to(ROOT).as_posix(),
            SUMMARY_JSON_PATH.relative_to(ROOT).as_posix(),
            SUMMARY_MD_PATH.relative_to(ROOT).as_posix(),
            (EXPERIMENT_DIR / f"{experiment_id}.json").relative_to(ROOT).as_posix(),
        ],
        "reproducibility": {
            "command": (
                "python tools/run_experimental_neural_dynamics.py "
                f"--holdout-draws {config['holdout_draws']} --minimum-training-draws {config['minimum_training_draws']} "
                f"--package-size {config['package_size']} --random-trials {config['random_trials']} "
                f"--frequency-pool-size {config['frequency_pool_size']} --recency-decay {config['recency_decay']} "
                f"--reservoir-size {config['reservoir_size']} --leak-rate {config['leak_rate']} "
                f"--spectral-radius {config['spectral_radius']} --input-scale {config['input_scale']} "
                f"--bias-scale {config['bias_scale']} --ridge-alpha {config['ridge_alpha']} "
                f"--score-power {config['score_power']} --seed {config['seed']}"
            ),
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
    policy = _policy(config)
    registry_rows = _read_registry()
    if write_outputs and register:
        registry_rows = _upsert_registry(experiment)
    elif register:
        registry_rows = [row for row in registry_rows if row.get("experiment_id") != experiment_id] + [experiment]
    report = {"policy": policy, "experiment": experiment, "registry_entries": len(registry_rows)}
    if write_outputs:
        _write_outputs(report, registry_rows)
    return report


def deterministic_signature(report: dict[str, Any]) -> str:
    experiment = report.get("experiment", {})
    return str((experiment.get("reproducibility") or {}).get("result_signature_sha256") or "")
