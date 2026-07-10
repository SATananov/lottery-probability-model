# Step 136 — Incident Evidence Recovery Drill & Restore Validation

Adds a fail-closed, isolated recovery drill for archived incident evidence bundles.

- Preview is read-only.
- Only registry-VERIFIED archives with matching SHA-256 are eligible.
- A precise confirmation phrase is required.
- The archive is copied into an isolated staging workspace and inspected again with Step 133.
- Bundle identity and checksums must match.
- No automatic restore to production/export folders is performed.
- The Step 134 append-only registry and Step 135 archive remain unchanged.
