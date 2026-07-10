# Step 131.4 — Operator Incident Guidance & Dashboard Final QA

This hardening step removes the ambiguous initial `Unavailable` presentation when no live BST request has been made.

The dashboard now exposes an explicit operational state:

- `not_checked` — no live request has been made;
- `online` — the official source is reachable and a draw was recognized;
- stage-specific incident codes for `index_fetch`, `index_parse`, `detail_fetch`, `detail_validation`, and `classification` failures.

Each failure state includes Bulgarian operator guidance describing the safe next action. The dashboard remains read-only and fail-closed. It does not ingest a draw, unlock production, refresh downstream modules, consume a token, or retrain models.
