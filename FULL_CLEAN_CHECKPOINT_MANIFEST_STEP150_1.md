# Full CLEAN Checkpoint Manifest — Step 150.1

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 150.1 — Deep Dynamic UI Localization & User-Friendly Table Repair`
- Generated (Europe/Sofia): `2026-07-12T12:36:42+03:00`
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

## Deep UI verification

- Static visible-text rows: `2060`
- Static visible-text failures: `0`
- Unique table headers: `791`
- Table-header failures: `0`
- Unique dynamic values: `628`
- User-facing dynamic failures: `0`
- Screenshot regression failures: `0`
- Technical fields hidden by default: `None`
- Protected Step 148 files: `True`
- Active lock: `LOCK-148-c299f383382d1f4a3ec7355f`
- Expected draw: `2026-54`

## Local checks

```powershell
python .\tools\audit_deep_ui_integrity.py
python .\scripts\verify_step_148.py
python .\scripts\verify_step_149.py
python .\scripts\verify_step_150_1.py
python .\tools\finalize_step_150_1_release.py --verify-only
python .\tools\finalize_step_150_1_release.py --build-zip

git status -sb
```

When applying the clean ZIP, restore `.git`, `.venv` and the trusted local journal from the previous local backup. Journal paths remain ignored and excluded from release packages.
