# Step 145.1 — Clean Release Metadata & Runtime Artifact Integrity Repair

## Причина

Одитът на пълното работно копие след Step 145 откри две отделни release слабости:

1. `release-manifest.json` включваше локалната `.venv`, въпреки че CLEAN manifest-ът заявяваше обратното.
2. Обикновена проверка при старт обновяваше tracked Step 122, Step 123 и Step 126 артефакти само заради timestamps, HTML diagnostics и идентични audit събития.

Това не променяше dataset-а или neural експеримента, но правеше release metadata недостоверна и оставяше ненужен Git шум.

## Поправка на release слоя

Добавен е единен policy engine:

- `src/v145_1_release_artifact_integrity.py`

Той управлява scope-а за Step 143.3, Step 144, Step 145 и Step 145.1. Забранени са:

- `.git`, `.venv`, `venv`, `.r-lib`;
- Python, pytest и Jupyter кешове;
- `reports/runtime/` и локални backups;
- `.env` и Streamlit secrets;
- ZIP, log, tmp, bak и backup файлове;
- build/dist и editor metadata.

Manifest verifier-ът проверява checkpoint, policy version, уникални пътища, забранени класове, размер, SHA-256, липсващи, stale и unlisted файлове.

Clean ZIP builder-ът създава един project root, след което изпълнява forbidden-path и CRC проверка.

Step 144/145 dataset identity вече нормализира CSV newline формата до историческия Windows CRLF формат преди SHA-256. Така съществуващите experiment IDs и result signatures се запазват, а read-only verification дава еднакъв резултат при Windows и Linux checkout.

## Поправка на runtime слоя

Добавен е:

- `src/v145_1_runtime_artifact_integrity.py`

Step 122, Step 123 и Step 126 вече:

- записват текущото volatile състояние в `reports/runtime/v145_1_artifact_integrity/`;
- използват atomic writes;
- обновяват tracked canonical snapshots само при semantic промяна;
- игнорират timestamps и други диагностични полета при semantic comparison;
- не добавят идентично Step 126 audit събитие при всяко стартиране;
- използват ignored runtime status за cache TTL между локални стартирания.

Semantic промени като нов официален тираж, различен operational status, грешка, промяна в configuration или реално downstream действие продължават да обновяват canonical evidence.

## Защитени области

Step 145.1 не променя:

- официалните и историческите draw datasets;
- личния SQLite дневник;
- обучените ML модели;
- Step 144 experiment registry резултатите;
- Step 145 neural dynamics резултата;
- production ticket pipeline.

Не е изпълнявано тежко ML преобучение.

## Проверка

```powershell
python .\scripts\verify_step_145_1.py
python .\tools\finalize_step_145_1_release.py --verify-only
python .\tools\finalize_step_145_1_release.py --build-zip
```

Успешният резултат е:

```text
STEP_145_1_VERIFY_OK
```
