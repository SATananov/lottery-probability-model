# Notebook Package Added — 2026-07-07

Добавен е структуриран ML notebook пакет към проекта.

## Added files

- `tools/create_ml_notebooks.py` — generator script за notebooks.
- `requirements-notebooks.txt` — optional dependencies за notebooks.
- `notebooks/README.md` — употреба и препоръчителен ред.
- `notebooks/00_project_overview.ipynb`
- `notebooks/01_data_overview_and_quality.ipynb`
- `notebooks/02_frequency_model.ipynb`
- `notebooks/03_gap_model.ipynb`
- `notebooks/04_pattern_balance_model.ipynb`
- `notebooks/05_combined_strategy.ipynb`
- `notebooks/06_ml_extensions.ipynb`
- `notebooks/07_model_comparison.ipynb`
- `notebooks/08_ensemble_and_weighting.ipynb`
- `notebooks/09_ticket_builder_and_portfolio.ipynb`
- `notebooks/10_backtest_and_performance.ipynb`
- `notebooks/11_explainability_and_conclusions.ipynb`

## Purpose

Тези notebooks са за описание, визуализация, таблици, графики и разбиране на ML/статистическите модели. Те не променят Streamlit приложението и не са runtime dependency за app-а.

## Data status preserved

- Latest draw in `data/historical_draws.csv`: 2026-07-05, draw 52, numbers 4, 11, 21, 28, 36, 49.
- Rows: 10062.

## Run

```powershell
cd "C:\Users\stana\Desktop\lottery-probability-model"
python -m pip install -r requirements-notebooks.txt
jupyter notebook
```

Or open `notebooks/` directly in VS Code.
