# Step 126 — Startup Automation and Operator Controls

Implemented:

- once-per-Streamlit-session startup check;
- disk cache TTL to prevent repeated network calls on rerun or restart;
- manual force check;
- persistent operator settings;
- optional safe Step 124 ingestion;
- optional Step 125 downstream refresh;
- no heavy ML retraining;
- status, report, summary and audit outputs;
- conservative defaults: auto-check enabled, auto-apply disabled.
