# CLEAN ZIP MANIFEST — STEP 128.1

Step 128.1 — Production Guardrails CLI Project Root Bootstrap Repair

Changed files:
- tools/run_production_guardrails_check.py
- scripts/verify_step_128.py
- reports/v128_1_cli_project_root_bootstrap_repair.md
- CLEAN_ZIP_MANIFEST_STEP128_1.md

Purpose:
- Fix `ModuleNotFoundError: No module named 'src'` when the Step 128 CLI is launched directly from `tools` on Windows.
- No production data changes.
- No guardrail behavior changes.
