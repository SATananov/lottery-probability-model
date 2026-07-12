# Lottery Probability Model 6/49

## За проекта

Това е **частен локален експеримент**, създаден за лично изучаване на историческите тиражи на Български спортен тотализатор — Тото 2, 6/49.

Проектът не е търговски продукт, публична услуга или система за гарантирано предсказване. Използва статистически анализи, сравнителни модели и локални помощни инструменти. При честен тираж всяка точна комбинация от 6 числа има еднаква теоретична вероятност — `1 към 13 983 816`.

Проектните данни, модели и отчети се изпълняват локално. Личният дневник е отделен от публичния release пакет и остава само на устройството на собственика.

## Авторски и експериментален контекст

Проектът е личен експериментален проект на **Стефан Тананов**. Той се развива итеративно чрез локални експерименти, собствени решения за структурата, проверка върху реални исторически данни и ръчно приемане на всяка завършена стъпка.

Изходният код и отчетите могат да бъдат редактирани с обичайни програмни инструменти, но нито един предложен или автоматично получен резултат не се приема без локална проверка. Историята на стъпките, verification скриптовете, manifest проверките и работните ограничения са част от доказуемия процес на разработка.

Проектът не твърди, че лотарийните тиражи са предвидими. Целта е обучение, експериментиране и изграждане на дисциплиниран статистически и софтуерен процес.

Подробна декларация за авторството и използваните помощни инструменти: `AUTHORSHIP_AND_TOOLING.md`.

## Текущо състояние

- Последен локален тираж: `2026-07-09`, тираж `53`.
- Последни числа: `12, 17, 23, 30, 38, 41`.
- Основен набор от данни: `10063` реда.
- Синхронизирани слоеве:
  - `data/historical_draws.csv`
  - `data/v40_normalized_draw_events.csv`
  - `data/v41_canonical_draw_events.csv`
- Стандартен пакет: `3` фиша × `4` реда = `12` комбинации.
- Локален дневник: SQLite база в `data/user_journal.db`, игнорирана от Git и изключена от clean release архивите.
- Модулът за производствени операции е затворен и по подразбиране остава заключен.

## Изисквания

- Windows 10/11
- Python 3.11
- PowerShell или Command Prompt
- Интернет е необходим само за инсталиране на зависимости и за официална БСТ синхронизация.

## Инсталиране в чиста среда

От основната директория на проекта:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python tools/verify_clean_environment.py
```

Пакетите за Jupyter notebooks са по избор:

```powershell
python -m pip install -r requirements-notebooks.txt
```

R анализите не изискват включена `.r-lib`. При нужда R пакетите се инсталират локално според използваната R среда.

## Стартиране

Препоръчително:

```powershell
python -m streamlit run app.py
```

Алтернативно:

```powershell
python -m streamlit run streamlit_app.py
```

Стандартният локален адрес е:

```text
http://localhost:8501
```

Могат да се използват и включените Windows стартови файлове:

```text
START_LOTTERY_CHROME_SIMPLE.bat
start_lottery_app.bat
```

## Основна структура

```text
lottery-probability-model/
├── app.py                    # Поддържан Streamlit entrypoint
├── streamlit_app.py          # Основно приложение
├── requirements.txt          # Зависимости за изпълнение
├── requirements-notebooks.txt
├── configs/                  # Настройки на моделите
├── data/                     # Набори от данни, официални източници и публична journal схема
├── models/                   # Моделни и работни артефакти
├── notebooks/                # Аналитични notebooks
├── r/                        # R скриптове
├── reports/                  # Анализи и отчети от проверките
├── scripts/                  # Скриптове за изграждане и проверка
├── src/                      # Основни Python модули
├── streamlit_pages/          # Допълнителни UI секции
└── tools/                    # Операторски и диагностични инструменти
```

## Основни проверки

```powershell
python audit_dataset.py
python tools/verify_clean_environment.py
python scripts/verify_step_140.py
python scripts/verify_step_141.py
```

## Обновяване на официалните данни

Проверка без запис:

```powershell
python tools/sync_bst_official_latest.py --recent 5
```

Проверка и запис:

```powershell
python tools/sync_bst_official_latest.py --recent 5 --write
```

След официална синхронизация слоят с данни за моделите може да се обнови с:

```powershell
python tools/refresh_model_data_after_bst_sync.py --write
```

Автоматично тежко преобучение не се изпълнява без изрично операторско действие.

## Обучение и анализ

```powershell
python train_model.py
python train_cold_model.py
python train_middle_model.py
python train_gap_model.py
python train_combined_model.py
python train_advanced_model.py
python train_ml_extensions.py
python predict_next_draw.py
```

Аналитичните notebooks се намират в `notebooks/` и могат да се отворят с VS Code или Jupyter.

## Локална безопасност

Проектът е предназначен за лично локално ползване. Не се препоръчва Streamlit приложението да бъде публикувано в интернет без отделна защита за достъп.

Вградените производствени операции използват заключване, изрично съгласие на оператора и пробни проверки без промяна. След чист контролен пакет състоянието трябва да остане:

```text
production_locked = true
operator_consent_granted = false
auto_apply_enabled = false
auto_refresh_enabled = false
```

## Правила за чист контролен пакет

В чистия архив се пазят работещият код, наборите от данни, моделните артефакти, отчетите, notebooks, оригиналните официални източници и публичната схема на локалния дневник.

Не се включват:

```text
.git/
.venv/
.r-lib/
__pycache__/
*.pyc
.pytest_cache/
.ipynb_checkpoints/
временни ZIP архиви, резервни копия и log файлове
стари междинни CLEAN manifest файлове
личният `data/user_journal.db` и `data/user_journal_exports/`
```

## Step 141

Step 141 добавя:

- проверка за чиста Python среда;
- синхронизиран README и release metadata;
- директно декларирана `altair` dependency;
- граници за съвместимост за пакетите за изпълнение и фиксиран `scikit-learn==1.8.0` за наличните моделни артефакти;
- премахване на локалната `.r-lib` библиотека и излишните checkpoint manifests;
- проверка за временни файлове и нежелани служебни обозначения от използвани инструменти;
- нов manifest на чистия ZIP архив с SHA-256 checksums.

Подробности: `reports/STEP_141_CLEAN_ENVIRONMENT_AND_DOCUMENTATION_SYNC.md`.

## Step 143

След успешно прилагане на нов официален тираж проектът автоматично обновява R статистическия анализ, статистическите характеристики, решението за игра и двата фиш пакета. Финалната проверката за актуалност потвърждава синхронизацията.

Тежкото ML преобучение не се изпълнява автоматично и остава отделна ръчна операция.

Подробности: `reports/STEP_143_AUTOMATIC_LIGHTWEIGHT_DOWNSTREAM_REFRESH_AFTER_OFFICIAL_DRAW.md`.

## Step 143.1

Step 143.1 подобрява описанието на личния експериментален контекст, езиковата последователност и целостта на release пакета. Коригирани са видимо повредени смесени изречения в генератори и артефакти, а verification пътищата на Step 122 и Step 125 са направени read-only при тестово изпълнение.

Добавен е и критичен research note за непрекъснати невронни динамични системи. Методът не е внедрен в проекта и е оставен само като възможна бъдеща експериментална посока.

Подробности:

- `PROJECT_CONTEXT.md`
- `reports/STEP_143_1_PERSONAL_PROJECT_DOCUMENTATION_LANGUAGE_AND_RELEASE_INTEGRITY.md`
- `reports/RESEARCH_NOTE_NEURAL_DYNAMICAL_SYSTEMS_REFERENCE.md`

## Step 143.2

Step 143.2 добавя контролиран audit за GitHub синхронизацията след нов официален тираж. Преди запис се заснема Git baseline, staging се ограничава до одобрения `data/models/reports` scope, а личният дневник, secrets, backups и несвързани локални промени не се включват.

След push локалният `HEAD` се сравнява с SHA, върнат от remote branch-а. Резултатът се пази като локален runtime audit в `reports/runtime/v143_2_git_sync/`; тази директория е изключена от Git, за да не оставя working tree мръсен след успешен sync.

Подробности: `reports/STEP_143_2_OFFICIAL_DRAW_GITHUB_SYNC_VALIDATION_AND_AUDIT.md`.

Read-only проверка от терминала:

```powershell
python tools/check_official_draw_github_sync.py
```

При локален commit с неуспешен push:

```powershell
python tools/check_official_draw_github_sync.py --retry-push
```

## Step 143.3

Step 143.3 добавя финално downstream обновяване до **нулеви блокери**. Операцията се приема за успешна само когато Step 122 потвърди `overall_status = synced` и `blocking_out_of_sync_count = 0`.

Статистическият слой вече се стартира през cross-platform launcher. При наличен `Rscript` се използват оригиналните R скриптове; при липса се използва ясно обозначен детерминиран Python compatibility runner. Тежките ML модели не се преобучават, а личният SQLite дневник се защитава чрез byte-for-byte snapshot и restore.

Команди:

```powershell
python .\tools\run_downstream_zero_blocker_closure.py --strict
python .\scripts\verify_step_143_3.py
```

Подробности: `reports/STEP_143_3_FINAL_DOWNSTREAM_FRESHNESS_REPAIR_AND_ZERO_BLOCKER_CLOSURE.md`.

## Step 144

Step 144 добавя регистър на възпроизводимите експерименти и начална baseline лаборатория. Всеки експеримент заключва dataset SHA-256, последен тираж, configuration, random seed, walk-forward split, code hash, среда, резултати, artifacts и заключение.

Първият експеримент сравнява frequency baseline с множество uniform-random baseline опити върху хронологичен holdout. Target тиражът се добавя в историята едва след оценяването му, което защитава от future-data leakage.

Команди:

```powershell
python .\tools\run_reproducible_baseline_experiment.py
python .\tools\run_reproducible_baseline_experiment.py --read-only
python .\scripts\verify_step_144.py
```

Подробности: `reports/STEP_144_REPRODUCIBLE_EXPERIMENT_REGISTRY_AND_BASELINE_LABORATORY.md`.

## Step 145

Step 145 добавя изолиран neural dynamics sandbox. Реализацията използва детерминиран leaky reservoir с walk-forward ridge readout и го сравнява срещу frequency, recency-weighted и uniform-random baselines при еднакъв брой комбинации.

Експериментът е research-only. Той не е свързан с production pipeline или с генератора на реални фишове. Първият регистриран резултат не преминава promotion gate и е запазен като отрицателно експериментално доказателство.

Команди:

```powershell
python .\tools\run_experimental_neural_dynamics.py
python .\tools\run_experimental_neural_dynamics.py --read-only
python .\scripts\verify_step_145.py
```

Подробности: `reports/STEP_145_EXPERIMENTAL_NEURAL_DYNAMICS_SANDBOX_AND_BASELINE_COMPARISON.md`.

## Step 145.1

Step 145.1 поправя release metadata и volatile runtime артефактите. Всички finalizer-и от Step 143.3 нататък използват единен release policy, който изключва `.git`, локални среди, caches, runtime storage, secrets, ZIP/log/backup файлове и build artifacts. Manifest проверката вече отказва забранени пътища и валидира size, SHA-256, duplicates, stale и unlisted записи.

Step 122, Step 123 и Step 126 пазят текущите timestamps и diagnostics в Git-ignored `reports/runtime/v145_1_artifact_integrity/`. Tracked operational snapshots се обновяват само при реална semantic промяна, а идентична startup проверка вече не добавя нов canonical audit ред. Dataset SHA за Step 144/145 е стабилизиран между Windows CRLF и Linux LF checkout, без промяна на запазените experiment signatures.

Команди:

```powershell
python .\scripts\verify_step_145_1.py
python .\tools\finalize_step_145_1_release.py --verify-only
python .\tools\finalize_step_145_1_release.py --build-zip
```

Подробности: `reports/STEP_145_1_CLEAN_RELEASE_METADATA_RUNTIME_ARTIFACT_INTEGRITY_REPAIR.md`.

## Step 146

Step 146 разширява neural dynamics sandbox-а с контролирана robustness проверка: 3 неприпокриващи се исторически walk-forward периода по 120 тиража и 5 random seeds, или общо 15 runs. Добавени са recent-window frequency и frequency–recency blend baselines, 95% bootstrap confidence intervals, exact sign tests и stability проверки по seed и период.

Първият регистриран Step 146 резултат е сравнително стабилен между seed-овете, но не показва устойчиво превъзходство. Neural mean е `2.012222`, а uniform-random mean е `2.073611`; 95% CI на neural-minus-random разликата е изцяло под нулата. Promotion gate остава блокиран и няма production интеграция.

Команди:

```powershell
python .\tools\run_controlled_neural_robustness.py
python .\tools\run_controlled_neural_robustness.py --read-only
python .\scripts\verify_step_146.py
python .\tools\finalize_step_146_release.py --verify-only
```

Подробности: `reports/STEP_146_CONTROLLED_NEURAL_EXPERIMENT_EXPANSION_AND_ROBUSTNESS_VALIDATION.md`.


## Step 147

Step 147 обединява експерименталните доказателства от Step 144–146 в отделен research decision registry и machine-readable evidence matrix. Слоят проверява source signatures, dataset identity, leakage guardrails и promotion gates, без да преизпълнява тежко обучение и без да използва production pipeline или личния дневник.

Официалното решение е: production promotion остава `BLOCKED`, текущата neural конфигурация е `PAUSE_AND_ARCHIVE`, а повторно настройване върху вече видените holdout периоди е забранено. Следващ експеримент е допустим само при материално нова предварително регистрирана хипотеза, ясна primary metric/gate рамка и нов или недокоснат validation период.

## Step 148

Step 148 започва истински prospective forward-test прозорец върху бъдещи официални тиражи. Step 146 алгоритъмът, random seeds и параметрите са замразени, а Step 147 production block остава активен. Преди следващият тираж да влезе в canonical dataset се записва pre-draw lock с dataset SHA-256, target sequence, evaluation packages и immutable forecast signature.

Ledger-ът е append-only по operating policy и всеки event е свързан с предишния чрез SHA-256. Тиражи без валиден предварителен lock се изключват и никога не се backfill-ват. Протоколът цели 30 допустими бъдещи тиража с междинни milestone отчети след 10 и 20 и финален research decision след 30. Няма автоматично production promotion.

Команди:

```powershell
python .\tools\lock_next_draw_forecast.py
python .\tools\settle_locked_draw_forecast.py
python .\scripts\verify_step_148.py
python .\tools\finalize_step_148_release.py --verify-only
```

Подробности: `reports/STEP_148_PROSPECTIVE_FORWARD_TEST_LOCK_AND_UNTOUCHED_FUTURE_DRAW_LEDGER.md`.

## Step 149

Step 149 почиства текущото repository дърво без пренаписване на Git историята. Личният journal е изключен от tracking и release пакетите; raw source aliases и timestamp-only model snapshots са консолидирани; големите row-level Markdown backtest таблици са заменени с компактни възпроизводими summaries; добавена е ясна декларация за авторство и инструментална прозрачност.

Историческите `.r-lib`, journal и backup blobs остават предмет на отделна, изрично одобрена Step 149.1 операция за history rewrite.
