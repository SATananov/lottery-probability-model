# Step 133 — Incident Evidence Integrity & Chain-of-Custody Inspector

## Purpose

Step 133 adds a read-only verification layer for Step 132 incident evidence ZIP files. It confirms that the archive is structurally safe, that the manifest checksums match the packaged evidence, and that the bundle identity is consistent.

## Guarantees

- no extraction to the project filesystem;
- no production activation or ingestion;
- no downstream refresh or ML retraining;
- archive SHA-256 fingerprint for chain-of-custody handoff;
- manifest checksum validation;
- safe ZIP member path and size checks;
- required evidence file checks;
- bundle ID consistency checks;
- detection of non-redacted prohibited fields;
- fail-closed verdict on any failed check.

## Operator workflow

Open **Production Operations Dashboard → Incident evidence → Evidence integrity inspector**, upload a Step 132 ZIP, and run the verification. A verified verdict is required before treating the bundle as trusted incident evidence.
