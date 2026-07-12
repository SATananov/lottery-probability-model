# Step 150.1 — Deep Dynamic UI Localization & User-Friendly Table Repair

Step 150.1 closes the runtime localization gaps found during the visual review after Step 150.

## Repair scope

- Localizes dynamic text loaded from JSON and CSV, not only Python string literals.
- Localizes every discovered CSV/DataFrame header through one central field dictionary.
- Localizes nested mappings shown with `st.json` and hides technical keys in normal-user mode.
- Converts internal method names and enum values to readable Bulgarian labels.
- Converts missing values such as `None` and `NaN` to `Няма данни`.
- Hides hashes, IDs, paths, UTC fields and signatures unless “Технически подробности” is enabled.
- Prevents metric values such as `БЛОКИРАНО`, `АКТИВНО` and `ПРЕМИНАТО` from being shortened with ellipses.
- Hides the current Streamlit toolbar/deploy controls from the normal user view.
- Keeps Bulgarian UTF-8/Cyrillic intact.
- Excludes the Git-ignored local journal database, local journal exports and runtime cache files from deterministic UI-audit counts.

## Visual regression examples fixed

- The Step 145 and Step 146 English interpretation messages are shown as natural Bulgarian sentences.
- `difference`, `Wins`, `Ties`, `Losses`, `Units`, `Confidence level` and bootstrap confidence columns are localized.
- `neural_dynamics_frozen_ensemble` is displayed as `Замразен ансамбъл с невронна динамика`.
- Empty forward-test results are displayed as `Няма данни`, not `None`.
- The active lock identifier remains available only in technical mode.

## Boundaries

This is a display-only change. The frozen Step 145/146 scoring engines, Step 148 prospective engine, active lock, ledger and personal local journal are not modified.
