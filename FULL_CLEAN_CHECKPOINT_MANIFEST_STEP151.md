# Full CLEAN Checkpoint Manifest — Step 151

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 151 — Repository Root Cleanup & Post-Draw Documentation Sync`
- Generated (Europe/Sofia): `2026-07-13T10:59:29+03:00`
- Base Git commit: `0e0858e Complete Step 151 repository root cleanup and post-draw documentation sync`
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `149.0`

## Repository cleanup

- Removed old root CLEAN manifests: `0`
- Remaining old root CLEAN manifests: `0`
- Documentation index: `docs/README.md`
- Step history: `docs/STEP_HISTORY.md`
- Root README is concise and current.
- Training scripts, application entrypoints and launchers remain in root because they are operational files.

## Post-draw synchronization

- Latest draw: `2026-54`
- Date: `2026-07-12`
- Numbers: `16, 29, 35, 37, 44, 47`
- Dataset rows: `10064`
- Step 148 settled draws: `1`
- Step 148 remaining draws: `29`
- Active lock: `LOCK-148-29ad1f2b8b69a3bc45e7de02`
- Expected draw: `2026-55`
- Production promotion remains blocked.

## Local checks

```powershell
python .\tools\audit_repository_root_cleanup.py
python .\scripts\verify_step_148.py
python .\scripts\verify_step_151.py
python .\tools\finalize_step_151_release.py --verify-only
python .\tools\finalize_step_151_release.py --build-zip
git status -sb
```

The personal journal database and exports remain local-only and are not included in the release manifest or clean ZIP.
