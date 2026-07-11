# Step 145 — Experimental Neural Dynamics Sandbox and Baseline Comparison

## Purpose

Step 145 turns the neural-dynamical-systems reference from Step 143.1 into a strictly isolated software experiment. It does not claim to implement analogue hardware, in-memory computing or an adaptive continuous ODE solver. The implemented model is a deterministic, continuous-time-inspired **leaky reservoir** with an online ridge-regression readout.

The experiment is part of the personal experimental project. Its purpose is to test whether a lightweight neural state representation adds measurable historical value beyond transparent baselines.

## Implemented state model

The hidden state follows the discrete leaky update:

```text
h_t = (1 - leak) h_(t-1) + leak tanh(W_in x_t + W_rec h_(t-1) + b)
```

The recurrent matrix is deterministically initialized from a fixed seed and scaled to a configured spectral radius. The output layer is a ridge-regression readout trained incrementally in chronological order.

This is inspired by continuous neural dynamics, but it is not presented as specialised neural hardware or as a numerical solver for a known physical differential equation.

## Walk-forward protocol

The default experiment uses:

- 9,823 initial training draws;
- 240 chronological holdout draws;
- 12 combinations per package;
- 50 uniform-random trials;
- a fixed seed;
- the same score-to-package builder for neural, frequency and recency scores;
- all 49 numbers in the candidate pool by default.

For every holdout draw:

1. the model and all baselines use only earlier draws;
2. the four packages are created before the target is revealed;
3. the target draw is scored;
4. only then is it added to the neural readout, frequency history and recency history.

## Baselines

Step 145 compares:

1. neural-dynamics reservoir;
2. expanding-window frequency scores;
3. exponentially recency-weighted scores;
4. multiple uniform-random trials.

All strategies use the same package size. The draw-level output is retained for paired comparisons.

## Statistical checks

The report contains:

- average best hits per draw;
- average total hits per package;
- hit distributions;
- neural-versus-frequency paired wins, ties and losses;
- neural-versus-recency paired wins, ties and losses;
- exact two-sided sign-test p-values;
- percentile and empirical one-sided p-value against the random-trial distribution.

The promotion gate is deliberately strict. Passing it would still not authorize production integration; it would only justify further research.

## Initial result

The initial default run did **not** pass the promotion gate:

- neural dynamics average best hits: **1.987500**;
- frequency baseline: **2.075000**;
- recency baseline: **2.054167**;
- uniform-random trial mean: **2.080333**;
- neural minus random mean: **-0.092833**;
- empirical p-value versus random trials: **1.000000**.

The negative result is preserved as first-class experimental evidence. The neural sandbox remains isolated and is not connected to real ticket generation.

## Artifacts

- `src/v145_experimental_neural_dynamics_engine.py`
- `src/v145_experimental_neural_dynamics_section.py`
- `tools/run_experimental_neural_dynamics.py`
- `models/v145_experimental_neural_dynamics_policy.json`
- `models/v145_experimental_neural_dynamics_status.json`
- `reports/v145_neural_dynamics_results.csv`
- `reports/v145_neural_dynamics_draw_comparison.csv`
- `reports/v145_neural_dynamics_summary.json`
- `reports/v145_neural_dynamics_summary.md`
- `reports/experiments/v145/<experiment_id>.json`
- `scripts/verify_step_145.py`

## Commands

Register the default experiment:

```powershell
python .\tools\run_experimental_neural_dynamics.py
```

Perform a deterministic read-only rerun:

```powershell
python .\tools\run_experimental_neural_dynamics.py --read-only
```

Verify Step 145:

```powershell
python .\scripts\verify_step_145.py
```

## Guardrails

- No personal journal access.
- No heavy ML retraining.
- No future-data leakage.
- No automatic production integration.
- No real-ticket generation.
- No claim of future predictive power or guaranteed profit.
