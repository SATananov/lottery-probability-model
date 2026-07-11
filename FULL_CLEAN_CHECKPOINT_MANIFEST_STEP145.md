# Full CLEAN Checkpoint Manifest — Step 145

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 145 — Experimental Neural Dynamics Sandbox and Baseline Comparison`
- Generated (Europe/Sofia): `2026-07-11T14:21:08+03:00`
- Base archive: `lottery-probability-model_STEP144_REPRODUCIBLE-EXPERIMENT-REGISTRY-BASELINE-LAB_FULL-CLEAN_20260711_134830.zip`
- Base archive SHA-256: `00659656db36ac82c63beaf6c46c6f5a0cd9d1534763ec19eae12a05dfd7e028`
- New Git commit: **not asserted** (`.git` is intentionally absent from a clean archive)

## Scope

- Adds a continuous-time-inspired leaky neural reservoir sandbox.
- Uses an online ridge readout in a strict expanding-window walk-forward protocol.
- Compares neural dynamics with frequency, recency-weighted and uniform-random baselines.
- Uses equal package sizes and stores draw-level paired comparison evidence.
- Registers the experiment in the Step 144 reproducibility registry.
- Preserves negative results and blocks automatic promotion.
- Does not use the personal journal, retrain heavy ML models or generate real tickets.
- Does not claim analogue neural hardware, in-memory computing or an adaptive ODE solver.

## Verification

- Step 122–144 verification chain: **PASS**
- Step 145 deterministic rerun: **PASS**
- Step 143.3 final freshness: **synced / zero blockers**
- Experiment ID: `EXP-145-0e11bccbcb-f2843280b3`
- Configuration SHA-256: `f2843280b3384c5130b5bee2dacfcd4340cb1e9c8459959920af897d0eff953d`
- Result signature SHA-256: `efcfc98d7674ddadf81443cb8cd35264b07913075f262ee5821b7ef77c38901f`
- Promotion gate passed: **False**
- Production integration enabled: **No**

## Local checks after applying in VS Code

```powershell
python ./tools/run_experimental_neural_dynamics.py --read-only
python ./scripts/verify_step_145.py
python ./tools/finalize_step_145_release.py --verify-only
git status -sb
```

After review, commit and push Step 145 before running a custom configuration.
