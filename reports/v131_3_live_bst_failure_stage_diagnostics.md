# Step 131.3 — Live BST Failure-Stage Diagnostics

This repair makes the read-only Production Operations Dashboard distinguish where a live BST check failed:

- `index_fetch` — DNS, TLS, timeout or other network access failure;
- `index_parse` — the official index was downloaded but no supported 6/49 candidate was recognized;
- `detail_fetch` — the draw candidate was found but its detail page could not be downloaded;
- `detail_validation` — the detail page was downloaded but the official record failed validation;
- `classification` — the validated draw could not be compared safely with the local source of truth.

The dashboard now carries the failure stage, exception type, connectivity flags and parser/source diagnostics. The change remains fail-closed and read-only: it does not ingest a draw, unlock production, refresh downstream modules or retrain ML models.
