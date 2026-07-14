# Step 151.2.1 — User-Facing Backup UI & Technical Details Separation Closure

Step 151.2.1 closes the remaining Step 150.2 regression on the Step 103 backup page.

## User-facing repair

The normal view now explains the page as **Application backup** rather than exposing release-engine terminology. It tells the user:

- what the backup is for;
- when it can be created;
- what the ZIP contains;
- that GitHub synchronization must be completed first;
- that the local played-ticket journal is not included.

The normal checks table uses plain labels and actions. The create button is disabled until the repository state is suitable for a reproducible backup.

## Technical separation

The following raw values are no longer visible when **Technical details** is disabled:

- `git status --short` output;
- terminal commands;
- raw internal check identifiers and fields;
- forbidden-file previews;
- raw result dictionaries and filesystem paths.

All of them remain available for diagnostics after enabling the existing global **Technical details** switch.

## Regression protection

The Step 151.2.1 verifier parses the page AST and rejects:

- unguarded `st.code`, `st.json`, or `st.exception` output;
- raw technical check tables in the normal view;
- reintroduction of the old developer-facing title and terminal block;
- raw developer terminology in normal user copy.

This step changes display and validation only. It does not change datasets, model training, scoring, Step 148 forecasts, or the personal journal.
