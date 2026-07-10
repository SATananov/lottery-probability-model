# Step 131.1 — Live BST Timeout Interface Repair

Changed files:
- `src/v131_production_operations_dashboard_engine.py`
- `scripts/verify_step_131.py`
- `reports/v131_1_live_bst_timeout_interface_repair.md`

Repair:
- Aligns Step 131 live BST call with Step 123 signature: `timeout=...`.
- Adds a verifier regression test for the live-check branch.
- No data migration, no draw ingestion, no downstream refresh, no ML retraining.
