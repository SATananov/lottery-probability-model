# Clean ZIP Manifest — Step 126

Project: lottery-probability-model
Step: 126 — Startup Automation and Operator Controls
Base checkpoint: Step 125 — Unified Downstream Refresh Pipeline

## Added

- `src/v126_startup_automation_engine.py`
- `src/v126_startup_automation_section.py`
- `tools/run_startup_automation.py`
- `scripts/verify_step_126.py`
- `models/v126_startup_automation_config.json`
- `reports/v126_startup_automation_implementation.md`

## Modified

- `streamlit_app.py`

## Safety defaults

- automatic startup check: enabled
- automatic official draw ingestion: disabled
- automatic downstream refresh: disabled
- heavy ML retraining: never started
- repeated Streamlit reruns: protected by session guard and disk cache TTL

## Verification

- `STEP_126_VERIFY_OK`
- `STEP_125_VERIFY_OK`
- `STEP_124_VERIFY_OK`
- `STEP_123_VERIFY_OK`
- `STEP_122_VERIFY_OK`
