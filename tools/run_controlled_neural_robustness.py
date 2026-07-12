from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v146_controlled_neural_robustness_engine import DEFAULT_CONFIG, run_controlled_neural_robustness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Step 146 controlled neural robustness validation")
    parser.add_argument("--read-only", action="store_true", help="Do not write reports or update the experiment registry")
    parser.add_argument("--fold-size", type=int, default=int(DEFAULT_CONFIG["fold_size"]))
    parser.add_argument("--fold-count", type=int, default=int(DEFAULT_CONFIG["fold_count"]))
    parser.add_argument("--seeds", default=",".join(str(value) for value in DEFAULT_CONFIG["seeds"]))
    parser.add_argument("--random-trials-per-run", type=int, default=int(DEFAULT_CONFIG["random_trials_per_run"]))
    args = parser.parse_args()

    config = json.loads(json.dumps(DEFAULT_CONFIG))
    config["fold_size"] = int(args.fold_size)
    config["fold_count"] = int(args.fold_count)
    config["seeds"] = [int(value.strip()) for value in str(args.seeds).split(",") if value.strip()]
    config["random_trials_per_run"] = int(args.random_trials_per_run)
    report = run_controlled_neural_robustness(
        config=config,
        write_outputs=not args.read_only,
        register=not args.read_only,
    )
    experiment = report["experiment"]
    comparison = experiment["results"]["comparison"]
    print(json.dumps({
        "experiment_id": experiment["experiment_id"],
        "result_signature_sha256": experiment["reproducibility"]["result_signature_sha256"],
        "promotion_gate_passed": comparison["promotion_gate_passed"],
        "run_count": experiment["results"]["split_policy"]["run_count"],
        "write_outputs": not args.read_only,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
