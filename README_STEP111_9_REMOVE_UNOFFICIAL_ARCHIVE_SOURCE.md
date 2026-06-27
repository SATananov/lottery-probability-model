# Step 111.9 — Remove Unofficial Archive Source

Този patch премахва видимия VirtBG / неофициален архив от app-а.

## Защо

След като данните за 2026 са въведени от официални БСТ screenshots, user-facing app-ът не трябва да показва неофициален архив като активен източник. Оставяме само проверената БСТ ръчна история.

## Какво прави

- Премахва страницата „Исторически архив на печалби“ от менюто.
- Премахва wrapper-а за Step 111.7 от `streamlit_app.py`.
- Премахва файловете на Step 111.7, ако са налични.
- Премахва VirtBG редове от `data/prize_winner_history.csv`, export CSV и SQLite, ако са налични.
- Запазва проверената история 2026 от Step 111.8.

## Проверка

```powershell
python -m compileall -q streamlit_app.py src scripts
python .\scripts111_9_remove_unofficial_archive_source.py
```

Очаквано:

```text
STEP_111_9_STATUS OFFICIAL_ONLY_PRIZE_SOURCE_READY
BLOCKING_FAILURES 0
```
