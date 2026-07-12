# Full CLEAN Checkpoint Manifest — Step 150.2

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 150.2 — Plain Bulgarian User Language & Complete Technical Separation`
- Generated (Europe/Sofia): `2026-07-12T13:20:59+03:00`
- Base Git commit: `6007b31`
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `149.0`

## Scope

- Applies a plain-language Bulgarian layer across all active Streamlit modules.
- Converts dynamic decision keys and requirements into complete user-facing sentences.
- Replaces wide technical research tables with concise normal-mode summaries.
- Keeps full statistical and cryptographic details in separate technical expanders.
- Prevents unknown English dynamic prose from appearing in Bulgarian normal mode.
- Enforces strict UTF-8 decoding and Cyrillic integrity for active UI files.
- Preserves personal journal privacy and the Step 148 prospective lock.
- Does not change model training, production scoring or historical results.

## Verification

- Broad static literal rows: `2060`
- Active UI literals: `1892`
- Active UI literal failures: `0`
- Dynamic keys and headers: `2936`
- Dynamic key failures: `0`
- Screenshot regression failures: `0`
- UTF-8 files checked: `112`
- UTF-8 failures: `0`
- Protected Step 148 files: `True`
- Active lock: `LOCK-148-c299f383382d1f4a3ec7355f`
- Expected draw: `2026-54`

## Local checks

```powershell
python .\tools\audit_plain_language_ui.py
python .\scripts\verify_step_148.py
python .\scripts\verify_step_149.py
python .\scripts\verify_step_150_2.py
python .\tools\finalize_step_150_2_release.py --verify-only
python .\tools\finalize_step_150_2_release.py --build-zip

git status -sb
```

When applying the clean ZIP, restore `.git`, `.venv` and the trusted local journal from the previous local backup. Journal paths remain ignored and excluded from release packages.
