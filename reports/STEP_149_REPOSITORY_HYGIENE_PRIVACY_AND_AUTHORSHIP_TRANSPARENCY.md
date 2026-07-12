# Step 149 — Repository Hygiene, Privacy & Authorship Transparency

## Scope

This step cleans the current repository tree with a normal commit. It does **not** rewrite Git history and does not force-push.

## Privacy repair

- `data/user_journal.db` is no longer part of the public/release tree.
- `data/user_journal_exports/` is no longer part of the public/release tree.
- Both paths are Git-ignored and release-forbidden.
- `data/user_journal_schema.sql` documents the empty public schema.
- A user may restore a trusted personal journal locally after applying a clean ZIP; Git and release tooling will continue to exclude it.

## Safe cleanup result

- Comparable release-scope files before cleanup: **1,433**
- Comparable release-scope files after cleanup: **1,188**
- Files removed: **265**
- Raw aliases removed: **238**
- Timestamp-only model snapshots removed: **19**
- Exact duplicate groups before: **106**
- Exact duplicate groups after: **35**
- Redundant bytes after: **302,415**

The remaining exact JSON mirrors are retained temporarily because old UI/report modules still address both model and report paths. They are listed in `reports/v149_remaining_exact_duplicate_groups.csv` and should be migrated before deletion.

## Report and source consolidation

- The raw archive now retains official files for 1958–2016 and one canonical yearly source for 2017–2025.
- The importer reads both canonical directories.
- Timestamp-only model snapshots are suppressed on future writes by semantic hashing.
- Four row-level Markdown backtests now contain compact summaries and a small first/last sample. Full detail remains reproducible by rerunning the scripts.
- The byte-identical duplicate launcher was removed.
- The legacy freshness and end-to-end validation layers now treat the journal export as an optional local artifact rather than a public required source.
- Heavy verifier entry points terminate deterministically after reporting their result, preventing lingering Python processes on some platforms.

## Authorship and tooling

No vendor-specific generative-AI SDK or external AI runtime dependency is present. The project includes `AUTHORSHIP_AND_TOOLING.md`, which identifies the personal author and explains that ordinary editing/review tools may assist without claiming autonomous authorship or unsupported fully-manual provenance.

Explicit branded vendor-marker hits found by this current-tree scan: **0**.

## Step 148 preservation

- Active lock: `LOCK-148-c299f383382d1f4a3ec7355f`
- Frozen Step 145/146/148 code and Step 148 policy/status/ledger/lock hashes: **PASS**
- Personal journal accessed by Step 148: **No**
- Production promotion: **Blocked**

## Deferred work

Historical `.r-lib`, journal, export and backup blobs remain reachable from old Git commits. Removing them requires the separately approved **Step 149.1** history rewrite and force-push. Step 149 intentionally does not perform that operation.
