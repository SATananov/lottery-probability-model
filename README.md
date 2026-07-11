# Lottery Probability Model 6/49

## За проекта

Това е **частен локален експеримент**, създаден за лично изучаване на историческите тиражи на Български спортен тотализатор — Тото 2, 6/49.

Проектът не е търговски продукт, публична услуга или система за гарантирано предсказване. Използва статистически анализи, сравнителни модели и локални помощни инструменти. При честен тираж всяка точна комбинация от 6 числа има еднаква теоретична вероятност — `1 към 13 983 816`.

Всички данни, модели, отчети и настройки се използват локално и остават под контрола на собственика на проекта.

## Авторски и експериментален контекст

Проектът е личен експериментален проект на **Стефан Тананов**. Той се развива итеративно чрез локални експерименти, собствени решения за структурата, проверка върху реални исторически данни и ръчно приемане на всяка завършена стъпка.

Изходният код и отчетите могат да бъдат редактирани с обичайни програмни инструменти, но нито един автоматично получен резултат не се приема без локална проверка. Историята на стъпките, verification скриптовете, manifest проверките и работните ограничения са част от доказуемия процес на разработка.

Проектът не твърди, че лотарийните тиражи са предвидими. Целта е обучение, експериментиране и изграждане на дисциплиниран статистически и софтуерен процес.

## Текущо състояние

- Последен локален тираж: `2026-07-09`, тираж `53`.
- Последни числа: `12, 17, 23, 30, 38, 41`.
- Основен набор от данни: `10063` реда.
- Синхронизирани слоеве:
  - `data/historical_draws.csv`
  - `data/v40_normalized_draw_events.csv`
  - `data/v41_canonical_draw_events.csv`
- Стандартен пакет: `3` фиша × `4` реда = `12` комбинации.
- Локален дневник: SQLite база в `data/user_journal.db`.
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
start_lottery_app_stable.bat
```

## Основна структура

```text
lottery-probability-model/
├── app.py                    # Поддържан Streamlit entrypoint
├── streamlit_app.py          # Основно приложение
├── requirements.txt          # Зависимости за изпълнение
├── requirements-notebooks.txt
├── configs/                  # Настройки на моделите
├── data/                     # Набори от данни, оригинални снимки на източника и дневник
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

В чистия архив се пазят работещият код, наборите от данни, моделните артефакти, отчетите, notebooks, оригиналните официални източници и локалният дневник.

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
```

## Step 141

Step 141 добавя:

- проверка за чиста Python среда;
- синхронизиран README и release metadata;
- директно декларирана `altair` dependency;
- граници за съвместимост за пакетите за изпълнение и фиксиран `scikit-learn==1.8.0` за наличните моделни артефакти;
- премахване на локалната `.r-lib` библиотека и излишните checkpoint manifests;
- проверка за временни файлове и нежелани нежелани служебни обозначения от използвани инструменти;
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
