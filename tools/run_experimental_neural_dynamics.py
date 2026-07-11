from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v145_experimental_neural_dynamics_engine import DEFAULT_CONFIG, run_experimental_neural_dynamics


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Step 145 research-only neural dynamics sandbox")
    parser.add_argument("--holdout-draws", type=int, default=DEFAULT_CONFIG["holdout_draws"])
    parser.add_argument("--minimum-training-draws", type=int, default=DEFAULT_CONFIG["minimum_training_draws"])
    parser.add_argument("--package-size", type=int, default=DEFAULT_CONFIG["package_size"])
    parser.add_argument("--random-trials", type=int, default=DEFAULT_CONFIG["random_trials"])
    parser.add_argument("--frequency-pool-size", type=int, default=DEFAULT_CONFIG["frequency_pool_size"])
    parser.add_argument("--recency-decay", type=float, default=DEFAULT_CONFIG["recency_decay"])
    parser.add_argument("--reservoir-size", type=int, default=DEFAULT_CONFIG["reservoir_size"])
    parser.add_argument("--leak-rate", type=float, default=DEFAULT_CONFIG["leak_rate"])
    parser.add_argument("--spectral-radius", type=float, default=DEFAULT_CONFIG["spectral_radius"])
    parser.add_argument("--input-scale", type=float, default=DEFAULT_CONFIG["input_scale"])
    parser.add_argument("--bias-scale", type=float, default=DEFAULT_CONFIG["bias_scale"])
    parser.add_argument("--ridge-alpha", type=float, default=DEFAULT_CONFIG["ridge_alpha"])
    parser.add_argument("--score-power", type=float, default=DEFAULT_CONFIG["score_power"])
    parser.add_argument("--seed", type=int, default=DEFAULT_CONFIG["seed"])
    parser.add_argument("--read-only", action="store_true")
    args = parser.parse_args()

    report = run_experimental_neural_dynamics(
        holdout_draws=args.holdout_draws,
        minimum_training_draws=args.minimum_training_draws,
        package_size=args.package_size,
        random_trials=args.random_trials,
        frequency_pool_size=args.frequency_pool_size,
        recency_decay=args.recency_decay,
        reservoir_size=args.reservoir_size,
        leak_rate=args.leak_rate,
        spectral_radius=args.spectral_radius,
        input_scale=args.input_scale,
        bias_scale=args.bias_scale,
        ridge_alpha=args.ridge_alpha,
        score_power=args.score_power,
        seed=args.seed,
        write_outputs=not args.read_only,
        register=not args.read_only,
    )
    experiment = report["experiment"]
    results = experiment["results"]
    payload = {
        "experiment_id": experiment["experiment_id"],
        "result_signature_sha256": experiment["reproducibility"]["result_signature_sha256"],
        "dataset_latest_draw": experiment["dataset"]["latest_draw"],
        "neural_average_best_hits": results["neural_dynamics"]["average_best_hits"],
        "frequency_average_best_hits": results["frequency_baseline"]["average_best_hits"],
        "recency_average_best_hits": results["recency_baseline"]["average_best_hits"],
        "uniform_random_mean_average_best_hits": results["random_summary"]["average_best_hits_mean"],
        "promotion_gate_passed": results["comparison"]["promotion_gate_passed"],
        "write_outputs": not args.read_only,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
