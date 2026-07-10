# Clean ZIP Manifest — Step 131.3

Step 131.3 — Live BST Failure-Stage Diagnostics.

Changed files:
- `src/v123_bst_official_draw_detection_engine.py`
- `src/v131_production_operations_dashboard_engine.py`
- `src/v131_production_operations_dashboard_section.py`
- `scripts/verify_step_131_3.py`
- `reports/v131_3_live_bst_failure_stage_diagnostics.md`
- `CLEAN_ZIP_MANIFEST_STEP131_3.md`

Purpose: separate connectivity, parser, detail-fetch and detail-validation failures in the read-only operations dashboard while preserving fail-closed production behavior.
