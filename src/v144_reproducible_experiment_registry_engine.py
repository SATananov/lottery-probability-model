from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
REGISTRY_PATH = ROOT / "data" / "experiment_registry.jsonl"
POLICY_PATH = ROOT / "models" / "v144_reproducible_experiment_registry_policy.json"
STATUS_PATH = ROOT / "models" / "v144_reproducible_experiment_registry_status.json"
INDEX_CSV_PATH = ROOT / "reports" / "v144_experiment_registry_index.csv"
RESULTS_CSV_PATH = ROOT / "reports" / "v144_baseline_lab_results.csv"
SUMMARY_JSON_PATH = ROOT / "reports" / "v144_baseline_lab_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v144_baseline_lab_summary.md"
EXPERIMENT_DIR = ROOT / "reports" / "experiments" / "v144"

TOTAL_NUMBERS = 49
DRAW_SIZE = 6
DEFAULT_CONFIG: dict[str, int] = {
    "holdout_draws": 240,
    "minimum_training_draws": 500,
    "package_size": 12,
    "random_trials": 50,
    "frequency_pool_size": 18,
    "seed": 1442026,
}

SAFE_NOTE_BG = (
    "Лабораторията прави детерминиран walk-forward исторически тест с ясно отделен holdout период. "
    "Това е сравнение на baselines, а не доказателство за предвидимост и не е гаранция за печалба."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def load_draws(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Canonical dataset is missing: {path}")

    draws: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"year", "draw_number", "n1", "n2", "n3", "n4", "n5", "n6"}
        if not required.issubset(set(reader.fieldnames or [])):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"Canonical dataset missing columns: {missing}")
        for index, row in enumerate(reader, start=1):
            numbers = [_parse_int(row.get(f"n{i}")) for i in range(1, DRAW_SIZE + 1)]
            if any(number is None for number in numbers):
                continue
            clean = sorted(int(number) for number in numbers if number is not None)
            if len(clean) != DRAW_SIZE or len(set(clean)) != DRAW_SIZE or not all(1 <= number <= TOTAL_NUMBERS for number in clean):
                continue
            draws.append(
                {
                    "index": index,
                    "draw_event_id": str(row.get("draw_event_id") or index),
                    "year": _parse_int(row.get("year")) or 0,
                    "draw_number": _parse_int(row.get("draw_number")) or 0,
                    "date": str(row.get("date") or ""),
                    "numbers": clean,
                }
            )
    if not draws:
        raise ValueError("Canonical dataset contains no valid 6/49 draws")
    return draws


def _draw_key(draw: dict[str, Any]) -> str:
    return f"{draw.get('year')}-{draw.get('draw_number')}"


def dataset_descriptor(draws: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "path": DATASET_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(DATASET_PATH),
        "row_count": len(draws),
        "first_draw": _draw_key(draws[0]),
        "latest_draw": _draw_key(draws[-1]),
        "latest_draw_date": draws[-1].get("date", ""),
    }


def code_descriptor() -> dict[str, Any]:
    relative_paths = [
        "src/v144_reproducible_experiment_registry_engine.py",
        "tools/run_reproducible_baseline_experiment.py",
    ]
    rows: list[dict[str, Any]] = []
    for relative in relative_paths:
        path = ROOT / relative
        if path.exists():
            rows.append({"path": relative, "sha256": sha256_file(path)})
    return {"files": rows, "combined_sha256": canonical_hash(rows)}


def environment_descriptor() -> dict[str, Any]:
    packages: dict[str, str] = {}
    for package in ("numpy", "pandas", "scikit-learn", "streamlit"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = "not-installed"
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": packages,
    }


def _package_metrics(package: list[list[int]], actual_numbers: Iterable[int]) -> tuple[int, int]:
    actual = set(int(number) for number in actual_numbers)
    hits = [len(actual.intersection(combo)) for combo in package]
    return (max(hits) if hits else 0, sum(hits))


def _uniform_random_package(package_size: int, rng: random.Random) -> list[list[int]]:
    package: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    while len(package) < package_size:
        combo = tuple(sorted(rng.sample(range(1, TOTAL_NUMBERS + 1), DRAW_SIZE)))
        if combo in seen:
            continue
        seen.add(combo)
        package.append(list(combo))
    return package


def _weighted_sample_without_replacement(
    values: list[int],
    weights: list[float],
    count: int,
    rng: random.Random,
) -> list[int]:
    available = list(values)
    available_weights = list(weights)
    selected: list[int] = []
    for _ in range(min(count, len(available))):
        total = sum(max(0.0, value) for value in available_weights)
        if total <= 0:
            index = rng.randrange(len(available))
        else:
            target = rng.random() * total
            cumulative = 0.0
            index = len(available) - 1
            for candidate_index, weight in enumerate(available_weights):
                cumulative += max(0.0, weight)
                if target <= cumulative:
                    index = candidate_index
                    break
        selected.append(available.pop(index))
        available_weights.pop(index)
    return sorted(selected)


def _frequency_package(
    counts: Counter[int],
    package_size: int,
    pool_size: int,
    rng: random.Random,
) -> list[list[int]]:
    ranked = sorted(range(1, TOTAL_NUMBERS + 1), key=lambda number: (-counts.get(number, 0), number))
    pool = ranked[: max(DRAW_SIZE, min(TOTAL_NUMBERS, pool_size))]
    rank_weights = [float(len(pool) - index) for index in range(len(pool))]
    package: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    attempts = 0
    while len(package) < package_size and attempts < package_size * 200:
        attempts += 1
        combo = tuple(_weighted_sample_without_replacement(pool, rank_weights, DRAW_SIZE, rng))
        if len(combo) == DRAW_SIZE and combo not in seen:
            seen.add(combo)
            package.append(list(combo))
    if len(package) < package_size:
        fallback = _uniform_random_package(package_size, rng)
        for combo in fallback:
            key = tuple(combo)
            if key not in seen:
                seen.add(key)
                package.append(combo)
            if len(package) >= package_size:
                break
    return package[:package_size]


def _aggregate_trial(strategy: str, trial: int, best_hits: list[int], total_hits: list[int]) -> dict[str, Any]:
    draws = len(best_hits)
    return {
        "strategy": strategy,
        "trial": trial,
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


def evaluate_walk_forward_baselines(draws: list[dict[str, Any]], config: dict[str, int]) -> dict[str, Any]:
    holdout_draws = min(int(config["holdout_draws"]), len(draws) - int(config["minimum_training_draws"]))
    if holdout_draws <= 0:
        raise ValueError("Not enough draws for the requested training/holdout split")
    split_index = len(draws) - holdout_draws
    training_draws = draws[:split_index]
    holdout = draws[split_index:]

    frequency_counts: Counter[int] = Counter()
    for draw in training_draws:
        frequency_counts.update(draw["numbers"])

    frequency_best: list[int] = []
    frequency_total: list[int] = []
    random_best: list[list[int]] = [[] for _ in range(int(config["random_trials"]))]
    random_total: list[list[int]] = [[] for _ in range(int(config["random_trials"]))]

    for offset, draw in enumerate(holdout):
        absolute_index = split_index + offset
        frequency_rng = random.Random(int(config["seed"]) + 700_000_001 + absolute_index)
        frequency_package = _frequency_package(
            frequency_counts,
            int(config["package_size"]),
            int(config["frequency_pool_size"]),
            frequency_rng,
        )
        best, total = _package_metrics(frequency_package, draw["numbers"])
        frequency_best.append(best)
        frequency_total.append(total)

        for trial in range(int(config["random_trials"])):
            random_rng = random.Random(int(config["seed"]) + trial * 1_000_003 + absolute_index)
            random_package = _uniform_random_package(int(config["package_size"]), random_rng)
            best, total = _package_metrics(random_package, draw["numbers"])
            random_best[trial].append(best)
            random_total[trial].append(total)

        # Walk-forward rule: the current target draw enters the history only after scoring.
        frequency_counts.update(draw["numbers"])

    frequency_result = _aggregate_trial("frequency_walk_forward", 0, frequency_best, frequency_total)
    random_results = [
        _aggregate_trial("uniform_random", trial + 1, random_best[trial], random_total[trial])
        for trial in range(int(config["random_trials"]))
    ]
    random_average_values = [float(row["average_best_hits"]) for row in random_results]
    random_at_least_3_values = [float(row["at_least_3_percent"]) for row in random_results]
    frequency_average = float(frequency_result["average_best_hits"])
    percentile = (
        sum(value <= frequency_average for value in random_average_values) / len(random_average_values) * 100.0
        if random_average_values
        else 0.0
    )

    return {
        "split": {
            "policy": "expanding_window_walk_forward",
            "training_draws_initial": len(training_draws),
            "holdout_draws": len(holdout),
            "holdout_first_draw": _draw_key(holdout[0]),
            "holdout_last_draw": _draw_key(holdout[-1]),
            "target_draw_added_after_scoring": True,
            "data_leakage_guard": "At each holdout point, only strictly earlier draws are available to the frequency baseline.",
        },
        "frequency_baseline": frequency_result,
        "random_trials": random_results,
        "random_summary": {
            "trials": len(random_results),
            "average_best_hits_mean": round(statistics.fmean(random_average_values), 9),
            "average_best_hits_std": round(statistics.pstdev(random_average_values), 9),
            "average_best_hits_min": round(min(random_average_values), 9),
            "average_best_hits_max": round(max(random_average_values), 9),
            "at_least_3_percent_mean": round(statistics.fmean(random_at_least_3_values), 9),
        },
        "comparison": {
            "frequency_minus_random_mean_average_best_hits": round(
                frequency_average - statistics.fmean(random_average_values), 9
            ),
            "frequency_percentile_among_random_trials": round(percentile, 3),
            "interpretation": (
                "The frequency baseline is above the random-trial mean on this historical holdout. "
                "This is exploratory evidence only and does not establish future predictive power."
                if frequency_average > statistics.fmean(random_average_values)
                else "The frequency baseline does not exceed the random-trial mean on this historical holdout."
            ),
        },
    }


def _policy(config: dict[str, int]) -> dict[str, Any]:
    return {
        "step": 144,
        "name": "Reproducible Experiment Registry and Baseline Laboratory",
        "project_context": "Personal experimental statistics and software-engineering project",
        "default_configuration": config,
        "required_registry_fields": [
            "experiment_id",
            "created_at_utc",
            "last_run_at_utc",
            "dataset",
            "code",
            "configuration",
            "random_seed",
            "split_policy",
            "results",
            "artifacts",
            "reproducibility",
            "conclusion",
        ],
        "guardrails": {
            "future_data_leakage": "forbidden",
            "heavy_ml_retraining": "not_performed",
            "personal_journal_access": "not_used",
            "results_claim": "historical_experiment_only",
            "registry_update": "deterministic_upsert_by_experiment_id",
        },
        "safe_note_bg": SAFE_NOTE_BG,
    }


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
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered)
    REGISTRY_PATH.write_text(text, encoding="utf-8")


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


def _write_outputs(report: dict[str, Any], registry_rows: list[dict[str, Any]]) -> None:
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(json.dumps(report["policy"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = {
        "step": 144,
        "status": "completed",
        "experiment_id": report["experiment"]["experiment_id"],
        "registry_entries": len(registry_rows),
        "dataset_sha256": report["experiment"]["dataset"]["sha256"],
        "configuration_sha256": report["experiment"]["reproducibility"]["configuration_sha256"],
        "result_signature_sha256": report["experiment"]["reproducibility"]["result_signature_sha256"],
        "holdout_draws": report["experiment"]["split_policy"]["holdout_draws"],
        "random_trials": report["experiment"]["configuration"]["random_trials"],
        "heavy_ml_retraining_performed": False,
        "personal_journal_used": False,
        "future_data_leakage_detected": False,
        "safe_note_bg": SAFE_NOTE_BG,
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    experiment = report["experiment"]
    result_rows = [experiment["results"]["frequency_baseline"]] + experiment["results"]["random_trials"]
    csv_rows: list[dict[str, Any]] = []
    for row in result_rows:
        csv_rows.append({key: value for key, value in row.items() if key != "distribution"})
    _write_csv(
        RESULTS_CSV_PATH,
        csv_rows,
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
        for row in registry_rows
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

    summary = {
        "step": 144,
        "status": "completed",
        "experiment_id": experiment["experiment_id"],
        "dataset": experiment["dataset"],
        "configuration": experiment["configuration"],
        "split_policy": experiment["split_policy"],
        "frequency_baseline": experiment["results"]["frequency_baseline"],
        "random_summary": experiment["results"]["random_summary"],
        "comparison": experiment["results"]["comparison"],
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

    frequency = experiment["results"]["frequency_baseline"]
    random_summary = experiment["results"]["random_summary"]
    comparison = experiment["results"]["comparison"]
    lines = [
        "# Step 144 — Възпроизводим baseline експеримент",
        "",
        f"- Experiment ID: `{experiment['experiment_id']}`",
        f"- Dataset SHA-256: `{experiment['dataset']['sha256']}`",
        f"- Dataset latest draw: **{experiment['dataset']['latest_draw']}**",
        f"- Initial training draws: **{experiment['split_policy']['training_draws_initial']}**",
        f"- Holdout draws: **{experiment['split_policy']['holdout_draws']}**",
        f"- Package size: **{experiment['configuration']['package_size']}** combinations",
        f"- Random trials: **{experiment['configuration']['random_trials']}**",
        f"- Seed: **{experiment['random_seed']}**",
        "",
        "## Основни резултати",
        "",
        f"- Frequency baseline average best hits: **{frequency['average_best_hits']:.6f}**",
        f"- Uniform-random mean average best hits: **{random_summary['average_best_hits_mean']:.6f}**",
        f"- Difference: **{comparison['frequency_minus_random_mean_average_best_hits']:.6f}**",
        f"- Frequency percentile among random trials: **{comparison['frequency_percentile_among_random_trials']:.1f}%**",
        "",
        "## Възпроизводимост",
        "",
        f"- Configuration hash: `{experiment['reproducibility']['configuration_sha256']}`",
        f"- Code hash: `{experiment['code']['combined_sha256']}`",
        f"- Result signature: `{experiment['reproducibility']['result_signature_sha256']}`",
        f"- Command: `{experiment['reproducibility']['command']}`",
        "",
        "## Ограничения",
        "",
        SAFE_NOTE_BG,
        "",
        experiment["conclusion"],
        "",
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_reproducible_baseline_experiment(
    *,
    holdout_draws: int = DEFAULT_CONFIG["holdout_draws"],
    minimum_training_draws: int = DEFAULT_CONFIG["minimum_training_draws"],
    package_size: int = DEFAULT_CONFIG["package_size"],
    random_trials: int = DEFAULT_CONFIG["random_trials"],
    frequency_pool_size: int = DEFAULT_CONFIG["frequency_pool_size"],
    seed: int = DEFAULT_CONFIG["seed"],
    write_outputs: bool = True,
    register: bool = True,
) -> dict[str, Any]:
    config = {
        "holdout_draws": int(holdout_draws),
        "minimum_training_draws": int(minimum_training_draws),
        "package_size": int(package_size),
        "random_trials": int(random_trials),
        "frequency_pool_size": int(frequency_pool_size),
        "seed": int(seed),
    }
    if not 1 <= config["package_size"] <= 100:
        raise ValueError("package_size must be between 1 and 100")
    if not 1 <= config["random_trials"] <= 1000:
        raise ValueError("random_trials must be between 1 and 1000")
    if not DRAW_SIZE <= config["frequency_pool_size"] <= TOTAL_NUMBERS:
        raise ValueError("frequency_pool_size must be between 6 and 49")

    draws = load_draws()
    dataset = dataset_descriptor(draws)
    code = code_descriptor()
    results = evaluate_walk_forward_baselines(draws, config)
    deterministic_result = {
        "dataset_sha256": dataset["sha256"],
        "configuration": config,
        "split": results["split"],
        "frequency_baseline": results["frequency_baseline"],
        "random_summary": results["random_summary"],
        "random_trials": results["random_trials"],
        "comparison": results["comparison"],
    }
    config_hash = canonical_hash(config)
    result_signature = canonical_hash(deterministic_result)
    experiment_id = f"EXP-144-{dataset['sha256'][:10]}-{config_hash[:10]}"
    now = utc_now()
    experiment = {
        "experiment_id": experiment_id,
        "step": 144,
        "title": "Walk-forward frequency baseline versus uniform-random baseline",
        "status": "completed",
        "experiment_type": "reproducible_baseline",
        "created_at_utc": now,
        "last_run_at_utc": now,
        "dataset": dataset,
        "code": code,
        "environment": environment_descriptor(),
        "configuration": config,
        "random_seed": config["seed"],
        "split_policy": results["split"],
        "results": {
            "frequency_baseline": results["frequency_baseline"],
            "random_summary": results["random_summary"],
            "random_trials": results["random_trials"],
            "comparison": results["comparison"],
        },
        "artifacts": [
            REGISTRY_PATH.relative_to(ROOT).as_posix(),
            STATUS_PATH.relative_to(ROOT).as_posix(),
            RESULTS_CSV_PATH.relative_to(ROOT).as_posix(),
            SUMMARY_JSON_PATH.relative_to(ROOT).as_posix(),
            SUMMARY_MD_PATH.relative_to(ROOT).as_posix(),
            (EXPERIMENT_DIR / f"{experiment_id}.json").relative_to(ROOT).as_posix(),
        ],
        "reproducibility": {
            "command": (
                "python tools/run_reproducible_baseline_experiment.py "
                f"--holdout-draws {config['holdout_draws']} --minimum-training-draws {config['minimum_training_draws']} "
                f"--package-size {config['package_size']} --random-trials {config['random_trials']} "
                f"--frequency-pool-size {config['frequency_pool_size']} --seed {config['seed']}"
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
    }
    policy = _policy(config)
    registry_rows: list[dict[str, Any]] = _read_registry()
    if write_outputs and register:
        registry_rows = _upsert_registry(experiment)
    elif register:
        # Read-only mode reports the projected registry count without modifying the file.
        registry_rows = [row for row in registry_rows if row.get("experiment_id") != experiment_id] + [experiment]

    report = {"policy": policy, "experiment": experiment, "registry_entries": len(registry_rows)}
    if write_outputs:
        _write_outputs(report, registry_rows)
    return report


def deterministic_signature(report: dict[str, Any]) -> str:
    experiment = report.get("experiment", {})
    return str((experiment.get("reproducibility") or {}).get("result_signature_sha256") or "")
