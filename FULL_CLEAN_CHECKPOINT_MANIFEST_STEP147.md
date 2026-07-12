# Full CLEAN Checkpoint Manifest — Step 147

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 147 — Experimental Evidence Synthesis & Research Decision Gate`
- Generated (Europe/Sofia): `2026-07-12T08:40:34+03:00`
- Base Git commit: `d1a82f4` (`Step 146`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `145.1`

## Scope

- Synthesizes Step 144, Step 145 and Step 146 evidence without rerunning heavy experiments.
- Verifies source experiment identities, signatures and canonical dataset consistency.
- Creates a dedicated research decision registry separate from the experiment registry.
- Records a machine-readable evidence matrix and decision gate.
- Blocks production promotion because robust superiority is absent.
- Pauses and archives the current neural configuration.
- Forbids tuning the same configuration on already observed holdouts.
- Requires materially new preregistered hypotheses and untouched validation periods for future research.
- Preserves Step 145.1 release integrity and ignored runtime artifact policy.

## Recorded conclusion

No comparison in the Step 144–146 evidence chain demonstrates robust positive superiority. The current neural configuration is therefore paused and archived; production promotion remains blocked.

## Verification

- Previous verifier chain through Step 146: **PASS required**
- Step 147 deterministic read-only synthesis: **PASS required**
- Source signature and dataset consistency: **PASS required**
- Research decision registry integrity: **PASS required**
- Same-holdout retuning prohibition: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **1424**
- Release manifest SHA-256: `dd535c57aa61f568d8d0273199e73493afbc5081a228d075bd15a667f652c4b3`
- Heavy ML retraining performed: **No**
- Personal journal modified: **No**

## Local checks

```powershell
python .\scripts\verify_step_146.py
python .\scripts\verify_step_147.py
python .\tools\finalize_step_147_release.py --verify-only
python .\tools\finalize_step_147_release.py --build-zip

git status -sb
```

The generated archive is validated independently after creation. Its SHA-256 is printed by the finalizer and is intentionally not embedded into a file contained inside the same archive.
