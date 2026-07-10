# Step 123 — BST Official Draw Detection Foundation

Implemented a read-only official draw detector for Bulgarian Sports Totalizator 6/49.

## Scope

- Reads the official 6/49 result index.
- Detects the newest official draw candidate.
- Optionally fetches and validates the detailed official result page.
- Compares the official candidate with the local source of truth.
- Reports `up_to_date`, `update_available`, `local_ahead`, or `official_unavailable`.
- Writes only status/report artifacts when a real check is executed.
- Does not write draw CSV data.
- Does not refresh downstream modules.
- Does not retrain models.

## Safety boundary

Step 124 will own safe ingestion and rollback. Step 125 will own downstream refresh.
