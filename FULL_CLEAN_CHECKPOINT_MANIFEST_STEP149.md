# Full CLEAN Checkpoint Manifest — Step 149

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 149 — Repository Hygiene, Privacy & Authorship Transparency`
- Generated (Europe/Sofia): `2026-07-12T10:15:28+03:00`
- Base Git commit: `c221d85` (`Step 148`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `149.0`

## Scope

- Cleans the current repository tree with a normal commit.
- Does not rewrite Git history and does not require a force-push.
- Excludes personal journal data from Git and clean release packages.
- Preserves a public empty journal schema and local auto-initialization behavior.
- Consolidates safe exact aliases and timestamp-only snapshots.
- Keeps compatibility-bound JSON mirrors until their consumers are migrated.
- Documents authorship and tool assistance without claiming autonomous authorship.
- Preserves the Step 148 active forward-test lock and frozen scoring implementation.

## Cleanup state

- Files removed: `265`
- Raw aliases removed: `238`
- Model snapshots removed: `19`
- Remaining compatibility duplicate groups: `35`
- History rewrite performed: `False`
- History purge deferred to: `Step 149.1`

## Verification

- Step 144–148 regression verification: **PASS required**
- Step 149 privacy and hygiene verification: **PASS required**
- Release manifest validation: **PASS required**
- Personal journal exclusion: **PASS required**
- Step 148 immutable lock validation: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **1188**
- Release manifest SHA-256: `0c3bd39fa867e3e01134ee7caded74da29df4adebff1b11ea89b94fffcff554e`

## Local checks

```powershell
python .\scripts\verify_step_148.py
python .\scripts\verify_step_149.py
python .\tools\finalize_step_149_release.py --verify-only
python .\tools\finalize_step_149_release.py --build-zip

git status -sb
```

When applying a clean ZIP, restore `.git`, `.venv` and the trusted local `data/user_journal.db` / `data/user_journal_exports/` from the previous local backup. The journal paths remain ignored and excluded from future release packages.
