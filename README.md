# Lottery Probability Model 6/49

## За проекта

Това е **частен локален експеримент**, създаден за лично изучаване на историческите тиражи на Български спортен тотализатор — Тото 2, 6/49.

Проектът не е търговски продукт, публична услуга или система за гарантирано предсказване. Използва статистически анализи, сравнителни модели и локални помощни инструменти. При честен тираж всяка точна комбинация от 6 числа има еднаква теоретична вероятност — `1 към 13 983 816`.

Всички данни, модели, отчети и настройки се използват локално и остават под контрола на собственика на проекта.

## Текущо състояние

- Последен локален тираж: `2026-07-09`, тираж `53`.
- Последни числа: `12, 17, 23, 30, 38, 41`.
- Основен dataset: `10063` реда.
- Синхронизирани слоеве:
  - `data/historical_draws.csv`
  - `data/v40_normalized_draw_events.csv`
  - `data/v41_canonical_draw_events.csv`
- Стандартен пакет: `3` фиша × `4` реда = `12` комбинации.
- Локален journal: SQLite база в `data/user_journal.db`.
- Production operations модулът е затворен и по подразбиране остава заключен.

## Изисквания

- Windows 10/11
- Python 3.11
- PowerShell или Command Prompt
- Интернет е необходим само за инсталиране на зависимости и за официална БСТ синхронизация.

## Инсталиране в чиста среда

От project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python tools/verify_clean_environment.py
```

Notebook пакетите са по избор:

```powershell
python -m pip install -r requirements-notebooks.txt
```

R анализите не изискват bundled `.r-lib`. При нужда R пакетите се инсталират локално според използваната R среда.

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

Могат да се използват и включените Windows launcher файлове:

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
├── requirements.txt          # Runtime зависимости
├── requirements-notebooks.txt
├── configs/                  # Настройки на моделите
├── data/                     # Datasets, raw snapshots и journal
├── models/                   # Model и runtime artifacts
├── notebooks/                # Аналитични notebooks
├── r/                        # R скриптове
├── reports/                  # Анализи и verification отчети
├── scripts/                  # Build и verification скриптове
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

След официална синхронизация model data слой може да се обнови с:

```powershell
python tools/refresh_model_data_after_bst_sync.py --write
```

Автоматично тежко retraining не се изпълнява без изрично операторско действие.

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

Notebooks се намират в `notebooks/` и могат да се отворят с VS Code или Jupyter.

## Локална безопасност

Проектът е предназначен за лично локално ползване. Не се препоръчва Streamlit приложението да бъде публикувано в интернет без отделна защита за достъп.

Вградените production операции използват заключване, operator consent и dry-run проверки. След clean checkpoint състоянието трябва да остане:

```text
production_locked = true
operator_consent_granted = false
auto_apply_enabled = false
auto_refresh_enabled = false
```

## Clean checkpoint policy

В clean архива се пазят работещият код, datasets, model artifacts, reports, notebooks, official raw snapshots и локалният journal.

Не се включват:

```text
.git/
.venv/
.r-lib/
__pycache__/
*.pyc
.pytest_cache/
.ipynb_checkpoints/
временни ZIP/backup/log файлове
стари междинни CLEAN manifests
```

## Step 141

Step 141 добавя:

- проверка за чиста Python среда;
- синхронизиран README и release metadata;
- директно декларирана `altair` dependency;
- compatibility bounds за runtime пакетите и фиксиран `scikit-learn==1.8.0` за наличните model artifacts;
- премахване на локалната `.r-lib` библиотека и излишните checkpoint manifests;
- проверка за временни файлове и нежелани generator/tool attribution следи;
- нов clean ZIP manifest с SHA-256 checksums.

Подробности: `reports/STEP_141_CLEAN_ENVIRONMENT_AND_DOCUMENTATION_SYNC.md`.

## Step 143

След успешно прилагане на нов официален тираж проектът автоматично обновява R анализа, статистическите характеристики, решението за игра и двата фиш пакета. Финалната freshness проверка потвърждава синхронизацията.

Тежкото ML retraining не се изпълнява автоматично и остава ръчна операция.

Подробности: `reports/STEP_143_AUTOMATIC_LIGHTWEIGHT_DOWNSTREAM_REFRESH_AFTER_OFFICIAL_DRAW.md`.
