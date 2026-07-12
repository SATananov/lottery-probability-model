# Step 147 — Experimental Evidence Synthesis & Research Decision Gate

## Purpose

Step 147 converts the Step 144–146 experimental chain into a formal, reproducible research decision. It prevents repeated tuning of the same neural configuration on already observed holdout periods and keeps experimental evidence separate from the production ticket pipeline.

## Evidence chain

- Step 144: frequency walk-forward baseline versus uniform-random baseline.
- Step 145: single-holdout neural dynamics sandbox versus frequency, recency and random baselines.
- Step 146: three non-overlapping historical folds, five seeds, fifteen robustness runs, confidence intervals and stability checks.

All three source artifacts use the same canonical dataset identity and retain deterministic result signatures.

## Decision

No Step 144–146 comparison demonstrates robust positive superiority. One Step 146 comparison is marginally positive against frequency, but its confidence interval crosses zero and its seed/fold stability rates do not satisfy the preregistered gate. The comparison with uniform random is robustly negative.

Therefore:

- production promotion remains blocked;
- the current neural configuration is paused and archived;
- rerunning or tuning the same configuration on the same observed holdouts is forbidden;
- the next experiment must test a materially new hypothesis with preregistered metrics and an untouched or future validation period.

## Guardrails

- No production pipeline access.
- No real ticket generation.
- No personal journal access.
- No heavy ML retraining.
- No mutation of Step 144–146 source experiment artifacts.
- Negative evidence is retained and surfaced rather than overwritten.

## Reproduction

```powershell
python .\tools\build_experimental_evidence_decision.py --read-only
python .\scripts\verify_step_147.py
```
