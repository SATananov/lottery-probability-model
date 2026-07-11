# CLEAN ZIP MANIFEST — STEP 143.2

- Project: `lottery-probability-model`
- Checkpoint: `Step 143.2 — Official Draw → GitHub Sync Validation & Audit`
- Project files in archive: **1353**
- Release manifest entries: **1350**
- Release manifest SHA-256: `21683c5495850e28417a98de03d7f1ad6c520dc975902d8ffa05836db246bf74`
- Verification: `STEP_122_VERIFY_OK` through `STEP_143_VERIFY_OK`
- Additional verification: `STEP_143_1_VERIFY_OK`, `STEP_143_2_VERIFY_OK`
- Step 143.2 functional Git simulation: **PASS**
- Final Step 143.2 verifier side effects: **0 persistent project files**
- Historical draw data changed: **No**
- Personal journal database changed: **No**
- Binary model artifacts changed: **No**
- Heavy ML retraining performed: **No**
- Bundled `.git` / `.venv` / `.r-lib` / `__pycache__`: **No**
- Current downstream freshness: **out_of_sync** (4 blocking layers; unchanged by this step)

## Main additions

- `src/v143_2_official_draw_github_sync_audit_engine.py`
- `src/v143_2_official_draw_github_sync_section.py`
- `models/v143_2_official_draw_github_sync_policy.json`
- `reports/STEP_143_2_OFFICIAL_DRAW_GITHUB_SYNC_VALIDATION_AND_AUDIT.md`
- `scripts/verify_step_143_2.py`
- `tools/check_official_draw_github_sync.py`
- controlled integration in `src/add_draws_section.py`
- ignored local audit directory `reports/runtime/v143_2_git_sync/`

The real GitHub remote confirmation will be recorded on the next official draw. The included functional test uses a temporary isolated Git remote and does not contact the owner's GitHub repository.
