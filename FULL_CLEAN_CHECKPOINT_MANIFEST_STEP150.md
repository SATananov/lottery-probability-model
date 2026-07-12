# Full CLEAN Checkpoint Manifest — Step 150

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 150 — Global Bulgarian UI, Table Localization & Technical Detail Separation`
- Generated (Europe/Sofia): `2026-07-12T11:26:27+03:00`
- Base Git commit: `a1dc3e5`
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `149.0`

## Scope

- Applies one display-only language layer across the Streamlit module.
- Covers module-level widgets, sidebar, columns, containers, forms and tables.
- Separates user labels from technical identifiers and cryptographic signatures.
- Creates a dedicated research navigation group and interface-integrity page.
- Preserves personal journal privacy and Step 149 repository hygiene.
- Does not change model training, production scoring or Step 148 forward-test state.

## UI verification

- UI literal rows: `2060`
- Unique UI literals: `1721`
- Forbidden Bulgarian residual rows: `0`
- Mixed visible-language rows: `0`
- Mojibake findings: `0`
- Technical fields hidden by default: `True`
- Protected Step 148 files: `True`
- Active lock: `LOCK-148-c299f383382d1f4a3ec7355f`
- Expected draw: `2026-54`

## Local checks

```powershell
python .\tools\audit_ui_language_integrity.py
python .\scripts\verify_step_148.py
python .\scripts\verify_step_149.py
python .\scripts\verify_step_150.py
python .\tools\finalize_step_150_release.py --verify-only
python .\tools\finalize_step_150_release.py --build-zip

git status -sb
```

When applying the clean ZIP, restore `.git`, `.venv` and the trusted local journal from the previous local backup. Journal paths remain ignored and excluded from release packages.
