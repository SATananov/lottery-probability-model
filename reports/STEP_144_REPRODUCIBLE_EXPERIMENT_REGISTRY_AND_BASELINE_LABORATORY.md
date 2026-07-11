# Step 144 — Reproducible Experiment Registry and Baseline Laboratory

## Purpose

Step 144 introduces a reproducible experiment discipline for the personal experimental project. Each registered run records the exact dataset fingerprint, latest draw, configuration, seed, split policy, code fingerprint, environment, results, artifacts and conclusion.

The purpose is not to claim that lottery draws are predictable. The purpose is to make every experiment reviewable, repeatable and comparable with transparent baselines.

## Initial baseline experiment

The first registered experiment compares:

1. a deterministic expanding-window frequency baseline;
2. multiple deterministic uniform-random baseline trials with the same number of combinations.

The default package contains 12 combinations, matching the practical structure of three tickets with four lines each.

## Leakage protection

The holdout period is evaluated in chronological order. At each point, the frequency baseline can use only draws that occurred strictly before the target draw. The target is added to the frequency history only after it has been scored.

This makes the initial laboratory a real walk-forward historical test rather than a replay that sees future data.

## Reproducibility identity

A run is identified by:

- canonical dataset SHA-256;
- canonical configuration SHA-256;
- code SHA-256;
- fixed random seed;
- deterministic result signature SHA-256.

Running the same code with the same dataset and configuration must reproduce the same result signature.

## Registry artifacts

- `data/experiment_registry.jsonl`
- `models/v144_reproducible_experiment_registry_policy.json`
- `models/v144_reproducible_experiment_registry_status.json`
- `reports/v144_experiment_registry_index.csv`
- `reports/v144_baseline_lab_results.csv`
- `reports/v144_baseline_lab_summary.json`
- `reports/v144_baseline_lab_summary.md`
- `reports/experiments/v144/<experiment_id>.json`

## Commands

Run and register the default experiment:

```powershell
python .\tools\run_reproducible_baseline_experiment.py
```

Run a read-only reproducibility check:

```powershell
python .\tools\run_reproducible_baseline_experiment.py --read-only
```

Verify Step 144:

```powershell
python .\scripts\verify_step_144.py
```

## Guardrails

- No heavy ML retraining.
- No personal journal access.
- No future-data leakage in the baseline split.
- No claim of guaranteed or future predictive performance.
- Deterministic registry upsert prevents duplicate records for the same dataset and configuration.
