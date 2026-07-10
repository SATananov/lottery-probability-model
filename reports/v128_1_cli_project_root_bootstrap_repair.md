# Step 128.1 — CLI Project Root Bootstrap Repair

Repairs `tools/run_production_guardrails_check.py` for direct execution on Windows.

The tool now inserts the repository root into `sys.path` before importing from `src`, matching the established verifier pattern. No production data, guardrail configuration, checkpoint, or automation behavior is changed.
