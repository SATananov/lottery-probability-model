# Step 151.3 — Prize History Integrity, CAPTCHA Diagnostics and Freshness Repair

Status: **REPAIR_CODE_APPLIED_DATA_SYNC_PENDING**

## Repair scope

- Empty SQLite Prize History is hydrated from the non-empty canonical CSV.
- A partial/conflicting SQLite table cannot overwrite the canonical CSV.
- Canonical and journal CSV mirrors are staged, compared and promoted with rollback.
- Manual CSV imports require a valid date/year, six unique ascending numbers, an official matching BST URL, no duplicate draw keys, and contiguous new draws.
- Missing jackpot/winner/prize fields remain empty and cannot overwrite verified values with zeroes.
- BST CAPTCHA is reported as `captcha_blocked`, not as an index parser failure.
- Last validated official draw evidence is preserved from Step 123/126 runtime history.
- Step 120 now requires equal latest draw, no missing Prize History draws and no content conflicts.
- Step 131 counts every blocking freshness state, including `ahead` and `behind`.
- Step 124 can create a missing byte-identical journal mirror safely and blocks a mismatched mirror.
- The legacy BST sync action is routed through Step 124 safe ingestion.
- Modified CSV writers use canonical LF line endings.

## Intentionally not performed

- No draw 54 or draw 55 data was imported.
- No R/downstream artifacts were rebuilt.
- No Step 148 lock was settled or regenerated.
- No Git commit, push or clean checkpoint was created.

## Verification

Run:

```powershell
python scripts/verify_step_151_3.py
```

Expected result:

```text
STEP_151_3_VERIFY_OK
PRIZE_HISTORY_ROWS 30
STEP120_STATUS MODEL_DATA_OUT_OF_SYNC
STEP120_RELATIONS {"historical_draws": "ahead", "v40_normalized": "ahead", "v41_canonical": "ahead"}
CAPTCHA_STATUS captcha_blocked FAILURE_STAGE index_captcha
DASHBOARD_BLOCKERS 6
```

The out-of-sync result is expected until the separate data synchronization phase adds draws 54 and 55 to the authoritative Prize History and rebuilds the downstream layers.
