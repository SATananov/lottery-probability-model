# CLEAN ZIP MANIFEST — STEP 145.1

- Project: `lottery-probability-model`
- Checkpoint: `Step 145.1 — Clean Release Metadata & Runtime Artifact Integrity Repair`
- Base code checkpoint: `Step 145`, commit `f1060ef`
- Project files in archive: **1398**
- Release manifest entries: **1395**
- Release manifest SHA-256: `033b7500bcb62d1cfda73d039de0a8650ec0312c64888db25c01444cbc10867e`
- Release policy version: `145.1`
- Verification chain: `STEP_122_VERIFY_OK` through `STEP_145_VERIFY_OK`
- Integrity verification: `STEP_145_1_VERIFY_OK`
- Neural experiment result signature: `efcfc98d7674ddadf81443cb8cd35264b07913075f262ee5821b7ef77c38901f`
- Production integration enabled: **No**
- Heavy ML retraining performed: **No**
- Personal journal modified by Step 145.1: **No**
- Runtime cache included in archive: **No**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**
- Bundled `.pyc` / `.zip` / `.log` / backup artifacts: **No**

## Repair result

- All Step 143.3–145 release finalizers use one shared release-scope policy.
- `release-manifest.json` rejects forbidden paths instead of only omitting a few known folders.
- Startup checks write current volatile state under ignored `reports/runtime/` storage.
- Tracked Step 122, Step 123 and Step 126 snapshots update only when their semantic state changes.
- Step 126 audit history no longer appends an identical event on every application start.
- Clean ZIP generation performs post-build root, forbidden-path and CRC validation.
- Step 144/145 dataset identity is stable across Windows CRLF and Linux LF checkouts.
