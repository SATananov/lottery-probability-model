# Clean ZIP Manifest — Step 123

Project: `lottery-probability-model`

Checkpoint base:
- Step 122 — Unified Official Draw Freshness Layer
- Branch: `main`
- Base commit supplied by user after successful Step 122 push

Implemented:
- Step 123 — BST Official Draw Detection Foundation

Main files:
- `src/v123_bst_official_draw_detection_engine.py`
- `src/v123_bst_official_draw_detection_section.py`
- `tools/detect_latest_bst_official_draw.py`
- `scripts/verify_step_123.py`
- `reports/v123_bst_official_draw_detection_implementation.md`
- `streamlit_app.py`

Safety contract:
- Read-only official detection
- No draw CSV writes
- No downstream refresh
- No model retraining

Verification:
- `STEP_123_VERIFY_OK`
- `STEP_122_VERIFY_OK`
