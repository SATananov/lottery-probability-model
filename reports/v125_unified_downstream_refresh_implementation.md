# Step 125 — Unified Downstream Refresh Pipeline

Adds an ordered, fail-fast downstream refresh after safe official draw ingestion.

Order:
1. historical / normalized / canonical model-data sync
2. R statistical reports
3. Step 121 R feature integration
4. Step 115 Decision Center
5. Step 117 real ticket pack
6. Step 118 model-system ticket pack
7. Step 122 freshness recheck

Heavy ML retraining is deliberately excluded. A failed stage blocks all later stages and records an audit/status report.
