# Full CLEAN Checkpoint Manifest — Step 146

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 146 — Controlled Neural Experiment Expansion & Robustness Validation`
- Generated (Europe/Sofia): `2026-07-12T07:58:14+03:00`
- Base Git commit: `b1c02a1` (`Step 145.1`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `145.1`

## Scope

- Adds controlled multi-seed neural robustness validation.
- Uses three non-overlapping chronological holdout folds of 120 draws each.
- Uses five deterministic seeds and fifteen complete walk-forward runs.
- Compares neural dynamics with frequency, recency, recent-window frequency, frequency–recency blend and uniform-random mean baselines.
- Records deterministic 95% bootstrap confidence intervals, exact sign tests and stability rates by seed and fold.
- Preserves strict score-before-learn chronology for every target draw.
- Keeps neural experiments isolated from production ticket generation.
- Preserves Step 145.1 clean release and ignored runtime artifact policy.

## Recorded conclusion

The neural configuration is reasonably stable across seeds, but does not demonstrate robust superiority. The default Step 146 promotion gate is **BLOCKED**. This negative result is retained as valid experimental evidence.

## Verification

- Previous verifier chain through Step 145.1: **PASS required**
- Step 146 deterministic read-only reproduction: **PASS required**
- Step 146 multi-seed and multi-fold structure: **PASS required**
- Step 146 confidence and stability artifacts: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **1410**
- Release manifest SHA-256: `933a91c77143ee61809b8b209a1b4af3e279bbd3e3789eef9be11ed8ea962ada`
- Heavy ML retraining performed: **No**
- Personal journal modified: **No**

## Local checks

```powershell
python .\scripts\verify_step_145_1.py
python .\scripts\verify_step_146.py
python .\tools\finalize_step_146_release.py --verify-only
python .\tools\finalize_step_146_release.py --build-zip

git status -sb
```

The generated archive is validated independently after creation. Its SHA-256 is printed by the finalizer and is intentionally not embedded into a file contained inside the same archive.
