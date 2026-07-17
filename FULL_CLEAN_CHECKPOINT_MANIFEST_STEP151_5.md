# Full CLEAN Checkpoint Manifest — Step 151.5

- Generated: `2026-07-17T09:24:23+03:00`
- Parent Git: `bb8cc75 Repair Step 151.2.2 runtime import compatibility`
- Prize History rows: `32`
- Historical / normalized / canonical rows: `10065`
- Latest synchronized draw: `2026-55` — `5, 10, 17, 20, 42, 47`
- Freshness blockers: `0`
- Step 148 settled draws: `2 / 30`
- Active lock: `LOCK-148-77bd8de48241186a6f388cb4` for `2026-56`
- Heavy models unchanged: `Yes`
- Production promotion: `Blocked`
- Local journal and exports: `Excluded`

Final verification:

```powershell
python .\scripts\verify_step_151_5.py --require-synced
git status -sb
```

Accepted Git status: `## main...origin/main` with no additional lines.
