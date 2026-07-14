# Step 151.2 — Repository Synchronization, UI Runtime Repairs & Fresh-Clone Integrity Closure

Step 151.2 closes the local changes found after Step 151.1 and makes the Desktop project reproducible from Git.

## Repairs

- the global numeric `selectbox` formatter always returns text;
- the two Step 94 result downloads use separate Streamlit keys;
- the Training Center decodes only literal `\uXXXX` text and preserves real Bulgarian Unicode;
- Python child processes in the Training Center and post-draw sync layers are forced to UTF-8;
- Step 80 derives dataset expectations from the current historical source instead of a frozen old draw;
- Step 150 validates mutable Step 148 status, ledger and active lock dynamically instead of hardcoding the previous lock;
- tracked text is renormalized to LF according to `.gitattributes`.

## Repository contract

The accepted final state is:

```text
git status -sb
## main...origin/main
```

A separate fresh clone must pass:

```powershell
python .\scripts\verify_step_148.py
python .\scripts\verify_step_151_2.py --require-synced
python .\tools\finalize_step_151_2_release.py --verify-only
```

The local personal journal database and exports remain outside Git and are not included in the clean release.
