# Step 146 — Controlled Neural Experiment Expansion & Robustness Validation

## Purpose

Step 146 expands the Step 145 research-only neural dynamics sandbox into a controlled robustness protocol. The objective is not to search for an attractive single holdout result, but to test whether the observed performance survives changes in random initialization and historical evaluation period.

## Experimental design

- 3 non-overlapping chronological holdout folds.
- 120 draws per fold, 360 distinct historical target draws in total.
- 5 deterministic random seeds.
- 15 seed/fold robustness runs.
- Expanding-window walk-forward scoring.
- Each target draw is added to the training state only after it has been scored.
- 12 combinations per strategy for every target draw.
- 10 uniform-random package trials inside each seed/fold run.

## Compared strategies

1. Continuous-time-inspired leaky neural reservoir with online ridge readout.
2. Full-history frequency walk-forward baseline.
3. Exponentially weighted recency baseline.
4. Recent-window frequency baseline over the latest 104 earlier draws.
5. Equal-weight frequency–recency blend.
6. Uniform-random mean baseline.

## Statistical controls

For every baseline, Step 146 records:

- mean paired advantage across the 15 seed/fold units;
- deterministic 95% bootstrap confidence interval;
- two-sided exact sign test;
- proportion of seeds with positive mean advantage;
- proportion of historical folds with positive mean advantage.

The neural result must also remain within the configured maximum seed spread. Every gate must pass simultaneously. Automatic production promotion is disabled even when the exploratory gate passes.

## Recorded result

The default run is stable across seeds, but it does not show robust superiority:

- Neural mean average-best-hits: **2.012222**
- Frequency: **2.008333**
- Recency: **2.035000**
- Recent-window frequency: **2.017222**
- Frequency–recency blend: **2.035556**
- Uniform-random mean: **2.073611**

The neural-minus-random mean advantage is **-0.061389**, with a 95% bootstrap interval of approximately **[-0.085944, -0.033056]**. The interval is fully below zero. The promotion gate is therefore **BLOCKED**.

This negative result is retained as useful experimental evidence. It indicates that the tested neural dynamics configuration is reasonably seed-stable but does not outperform the stronger simple and random baselines across the controlled historical periods.

## Guardrails

- No production pipeline integration.
- No real ticket generation.
- No personal journal access.
- No heavy ML retraining.
- No future-data leakage.
- No claim of predictability or guaranteed winnings.

## Commands

```powershell
python .\tools\run_controlled_neural_robustness.py
python .\tools\run_controlled_neural_robustness.py --read-only
python .\scripts\verify_step_146.py
python .\tools\finalize_step_146_release.py --verify-only
```
