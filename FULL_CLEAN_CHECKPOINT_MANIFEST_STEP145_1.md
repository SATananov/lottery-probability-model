# Full CLEAN Checkpoint Manifest — Step 145.1

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 145.1 — Clean Release Metadata & Runtime Artifact Integrity Repair`
- Generated (Europe/Sofia): `2026-07-12T07:16:22+03:00`
- Base Git commit: `f1060ef` (`Step 145`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `145.1`

## Scope

- Replaces ad-hoc release filtering with a single reusable allow/deny policy.
- Excludes `.git`, Python/R environments, caches, runtime state, secrets, archives, logs, backups and build artifacts.
- Validates every manifest row for path safety, uniqueness, file size and SHA-256.
- Detects missing, stale and unlisted release files.
- Adds atomic metadata/runtime writes to avoid partially written JSON files.
- Keeps volatile startup state in `reports/runtime/v145_1_artifact_integrity/`, which is ignored by Git and excluded from release packages.
- Preserves tracked operational snapshots unless a draw, status, configuration or other semantic value changes.
- Keeps the Step 145 neural dynamics experiment unchanged and research-only.
- Preserves historical Step 144/145 experiment signatures through cross-platform CSV newline normalization.

## Verification

- Previous verifier chain through Step 145: **PASS**
- Step 145.1 release-policy verification: **PASS required**
- Step 145.1 runtime no-dirty-tree verification: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **1395**
- Release manifest SHA-256: `033b7500bcb62d1cfda73d039de0a8650ec0312c64888db25c01444cbc10867e`
- Heavy ML retraining performed: **No**
- Personal journal modified: **No**

## Local checks

```powershell
python ./scripts/verify_step_145_1.py
python ./tools/finalize_step_145_1_release.py --verify-only
python ./tools/finalize_step_145_1_release.py --build-zip

git status -sb
```

The generated archive is validated independently after creation. Its SHA-256 is printed by the finalizer and is intentionally not embedded into a file contained inside the same archive.
