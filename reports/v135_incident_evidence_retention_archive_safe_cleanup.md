# Step 135 — Incident Evidence Retention, Archive & Safe Cleanup Policy

Step 135 introduces a fail-closed lifecycle policy for Step 132 incident evidence ZIP copies while preserving the Step 134 append-only registry.

## Guardrails

- Preview/dry-run is the default.
- Only old bundles whose latest verdict is `VERIFIED` are eligible for archive.
- `INVALID` and unverified evidence remain protected.
- A minimum number of newest verified bundles remains active.
- Archive and cleanup require separate exact confirmation phrases.
- SHA-256 is rechecked immediately before every move or deletion.
- The registry JSONL is never deleted, compacted, or rewritten.
- Archive and cleanup actions are recorded in a separate Step 135 audit JSONL.
- Production draw, activation, refresh, and ML state are untouched.
