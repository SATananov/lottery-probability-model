# Full CLEAN Checkpoint Manifest — Step 144

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 144 — Reproducible Experiment Registry and Baseline Laboratory`
- Generated (Europe/Sofia): `2026-07-11T13:56:20+03:00`
- Base archive: `lottery-probability-model_STEP143_3_FINAL-DOWNSTREAM-ZERO-BLOCKER-CLOSURE_FULL-CLEAN_20260711_132000.zip`
- Base archive SHA-256: `a0755e32d4b646269e41827f80138070464de6fdb54120099241c8e3b7bcc6e9`
- New Git commit: **not asserted** (`.git` is intentionally absent from a clean archive)

## Scope

- Adds a deterministic experiment registry with JSONL and CSV indexes.
- Records dataset, code, configuration, seed, environment, split, results and artifacts.
- Adds an expanding-window walk-forward baseline laboratory.
- Compares a frequency baseline with uniform-random packages of equal size.
- Preserves negative and neutral results as first-class experimental evidence.
- Adds a Bulgarian Streamlit page and a terminal runner.
- Does not retrain heavy ML models and does not access the personal journal.

## Verification

- Step 122–143.3 verification chain: **PASS**
- Step 144 deterministic rerun verification: **PASS**
- Step 143.3 final freshness: **synced / zero blockers**
- Experiment ID: `EXP-144-0e11bccbcb-98bfe5488b`
- Dataset SHA-256: `0e11bccbcb47ae6d34f32c5e791ca76cf199aca2ebefe77798c16ab4b4fbc579`
- Configuration SHA-256: `98bfe5488b5bdeb2f939eb5d461dad1fa4f782dad590487a28c9c19ed67990fb`
- Result signature SHA-256: `6dfdb5c332d01bcfc0d5aaf7199f55e60d8909db0a1608f45bcc23bc9d997184`
- Registry entries: **1**
- Heavy ML retraining performed: **No**
- Personal journal used: **No**
- Future-data leakage detected: **No**

## Local checks after applying in VS Code

```powershell
python .\tools\run_reproducible_baseline_experiment.py --read-only
python .\scripts\verify_step_144.py
python .\tools\finalize_step_144_release.py --verify-only
git status -sb
```

After review, commit and push Step 144 before running a new custom experiment.
