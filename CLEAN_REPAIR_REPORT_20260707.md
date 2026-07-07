# Lottery Probability Model — Clean Repair 2026-07-07

This package repairs the clean review ZIP state after the latest draw data was left outside the previous clean archive.

## Fixed

- Restored `app.py` as the Streamlit entrypoint wrapper.
- Added the real draw `2026-07-02` with numbers `8, 9, 12, 18, 33, 38`.
- Synchronized:
  - `data/historical_draws.csv`
  - `data/v40_normalized_draw_events.csv`
  - `data/v41_canonical_draw_events.csv`
- Patched `scripts/v40_create_normalized_draw_events.py` so missing text fields remain empty strings instead of `nan`.
- Regenerated post-draw status outputs through v106/v107/v108.
- Regenerated v117/v117.1/v118 package outputs.
- Aligned Step 99 dashboard active-plan snapshot with the current 3-ticket / 12-line ready pack.
- Removed old `_clean_zip_diagnostics`, temporary patch folders, Python cache files, and the untracked Step 119 preview artifact.

## Current verified state

- Dataset rows: `10061`
- Latest draw: `2026-07-02 — 8, 9, 12, 18, 33, 38`
- v106: `POST_DRAW_SYNCED`, blocking failures `0`
- v107: `TRAINING_POLICY_READY`, blocking failures `0`
- v108: `USER_MENU_LIVE_STATUS_SYNCED`, blocking failures `0`
- v117: `Пакетът е готов`, `3` tickets × `4` lines = `12` lines, `10.80 EUR`
- v117.1: `ADD_DRAW_TICKET_PACK_PRICE_SYNC_READY`, blocking failures `0`
- v118: `MODEL_SYSTEM_TICKET_BUILDER_READY`, `12` combinations, `10.80 EUR`

## How to run

```powershell
pip install -r requirements.txt
streamlit run app.py
```
