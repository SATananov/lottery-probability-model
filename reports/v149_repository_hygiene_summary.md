# Step 149 repository hygiene summary

- Normal commit only; Git history was not rewritten.
- Personal journal database and exports are local-only, Git-ignored and release-forbidden.
- 238 raw source aliases, 19 timestamp-only model snapshots and one duplicate launcher were removed.
- Four large row-level Markdown backtests were replaced by compact reproducible summaries.
- Legacy freshness/validation checks were made compatible with a missing local journal export, and long-running verifier exits were hardened.
- Compatibility-bound model/report JSON mirrors remain listed for a later dependency migration.
- The active Step 148 lock and frozen scoring artifacts remain byte-for-byte unchanged.
- Historical privacy and `.r-lib` blobs still require the separately approved Step 149.1 history rewrite.

See `reports/STEP_149_REPOSITORY_HYGIENE_PRIVACY_AND_AUTHORSHIP_TRANSPARENCY.md` for the full audit and decision.
