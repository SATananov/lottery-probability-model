# Step 124 — Safe Official Draw Ingestion

Step 124 adds a controlled write boundary for one contiguous, validated official BST 6/49 draw.

## Guarantees

- requires a successfully detected and validated official draw;
- accepts only a strictly newer contiguous draw;
- blocks duplicates and draw gaps;
- creates timestamped backups of the primary and journal mirror CSV files;
- builds and validates staged output before promotion;
- promotes the primary and journal mirror as matching files;
- records every attempt in a JSONL audit journal;
- restores both original files when promotion fails;
- does not refresh normalized, canonical, R, decision, ticket, or ML artifacts.

## Runtime files

- `src/v124_safe_official_draw_ingestion_engine.py`
- `src/v124_safe_official_draw_ingestion_section.py`
- `tools/ingest_latest_bst_official_draw.py`
- `scripts/verify_step_124.py`

## Generated runtime locations

- backups: `data/backups/step124_official_draw_ingestion/`
- staging: `data/staging/step124_official_draw_ingestion/`
- audit: `reports/v124_safe_official_draw_ingestion_audit.jsonl`
- status: `models/v124_safe_official_draw_ingestion_status.json`
- summary: `reports/v124_safe_official_draw_ingestion_summary.md`

The generated backup, staging, audit, status, and summary artifacts appear only after an operator runs the ingestion flow.
