from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v144_reproducible_experiment_registry_engine import DEFAULT_CONFIG, run_reproducible_baseline_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or verify the Step 144 reproducible baseline experiment")
    parser.add_argument("--holdout-draws", type=int, default=DEFAULT_CONFIG["holdout_draws"])
    parser.add_argument("--minimum-training-draws", type=int, default=DEFAULT_CONFIG["minimum_training_draws"])
    parser.add_argument("--package-size", type=int, default=DEFAULT_CONFIG["package_size"])
    parser.add_argument("--random-trials", type=int, default=DEFAULT_CONFIG["random_trials"])
    parser.add_argument("--frequency-pool-size", type=int, default=DEFAULT_CONFIG["frequency_pool_size"])
    parser.add_argument("--seed", type=int, default=DEFAULT_CONFIG["seed"])
    parser.add_argument("--read-only", action="store_true", help="Run without writing registry or report artifacts")
    args = parser.parse_args()

    report = run_reproducible_baseline_experiment(
        holdout_draws=args.holdout_draws,
        minimum_training_draws=args.minimum_training_draws,
        package_size=args.package_size,
        random_trials=args.random_trials,
        frequency_pool_size=args.frequency_pool_size,
        seed=args.seed,
        write_outputs=not args.read_only,
        register=not args.read_only,
    )
    experiment = report["experiment"]
    output = {
        "status": experiment.get("status"),
        "experiment_id": experiment.get("experiment_id"),
        "dataset_latest_draw": (experiment.get("dataset") or {}).get("latest_draw"),
        "dataset_sha256": (experiment.get("dataset") or {}).get("sha256"),
        "result_signature_sha256": (experiment.get("reproducibility") or {}).get("result_signature_sha256"),
        "frequency_average_best_hits": (experiment.get("results") or {}).get("frequency_baseline", {}).get("average_best_hits"),
        "random_mean_average_best_hits": (experiment.get("results") or {}).get("random_summary", {}).get("average_best_hits_mean"),
        "registry_entries": report.get("registry_entries"),
        "write_outputs": not args.read_only,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if experiment.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
