# CLEAN ZIP Manifest — Step 141

## Checkpoint

`Step 141 — Clean Environment Verification & Documentation Sync`

## Release purpose

Private local experiment checkpoint after dependency verification, documentation synchronization and cleanup of non-portable or temporary artifacts.

## Verified state

- Core datasets synchronized at `10063` rows.
- Latest local draw: `2026-07-09`, draw `53`.
- Latest numbers: `12, 17, 23, 30, 38, 41`.
- Python source compilation: PASS.
- Step 140 verification: PASS.
- Step 141 verification: PASS.
- Clean runtime dependency installation: PASS.
- Joblib model load with `scikit-learn==1.8.0`: PASS.
- SQLite integrity: PASS.
- Streamlit headless health endpoint: PASS.
- Explicit generator/tool attribution scan: PASS.

## Cleanup

Excluded from the final archive:

- `.git/`
- `.venv/`
- `.r-lib/`
- Python and notebook caches
- temporary, backup and log files
- old intermediate CLEAN manifests

## Machine-readable integrity

`release-manifest.json` contains SHA-256 checksums for 1330 project files, excluding the manifest itself and this human-readable file.
