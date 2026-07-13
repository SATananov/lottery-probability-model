# Full CLEAN Checkpoint Manifest — Step 150.3

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 150.3 — User-Friendly Internal Version Label Cleanup`
- Generated (Europe/Sofia): `2026-07-12T13:58:34+03:00`
- Base Git commit: `Step 150.2 synchronized main`
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `149.0`

## Scope

- Removes internal V-number labels from all normal user-facing Streamlit output.
- Replaces versioned workflow and model phrases with plain Bulgarian descriptions.
- Applies the cleanup to metrics, tables, JSON values, captions and status messages.
- Keeps exact versions, paths and identifiers available in technical-details mode.
- Preserves personal journal privacy and the Step 148 prospective lock.
- Does not change model training, production scoring or historical results.

## Verification

- Python literals with internal version labels: `149`
- Remaining literal failures: `0`
- Dynamic values with internal version labels: `339`
- Remaining dynamic failures: `0`
- Screenshot regression failures: `0`
- Technical mode preserves internal versions: `True`
- Protected Step 148 files: `True`
- Active lock: `LOCK-148-c299f383382d1f4a3ec7355f`
- Expected draw: `2026-54`

## Local checks

```powershell
python .\tools\audit_user_version_labels.py
python .\scripts\verify_step_148.py
python .\scripts\verify_step_149.py
python .\scripts\verify_step_150_3.py
python .\tools\finalize_step_150_3_release.py --verify-only
python .\tools\finalize_step_150_3_release.py --build-zip

git status -sb
```

When applying the clean ZIP, restore `.git`, `.venv` and the trusted local journal from the previous local backup. Journal paths remain ignored and excluded from release packages.
