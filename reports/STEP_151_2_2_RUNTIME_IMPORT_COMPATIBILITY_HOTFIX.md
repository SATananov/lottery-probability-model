# Step 151.2.2 — Runtime Import Compatibility Hotfix

## Problem

After Step 151.2 replaced the old hard-coded `PROTECTED_STEP148_HASHES` mapping with dynamic ledger-aware validation, the Step 150.1 deep UI engine still imported the removed name. Streamlit therefore stopped during startup with `ImportError`.

## Repair

- exposes the dynamic Step 148 validation through the public `protected_step148_status()` API;
- updates the deep UI engine to use the public API;
- removes the stale constant import;
- verifies the complete Step 150 integrity import chain and the current Step 148 protected state;
- preserves the Step 151.2 repository guarantees and Step 151.2.1 user-facing UI separation.

No historical draw data, scoring logic, model output or personal journal content is changed.
