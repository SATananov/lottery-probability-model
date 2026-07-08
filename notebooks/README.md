# ML Notebooks

This folder contains explanatory and analytical notebooks for the Lottery Probability Model 6/49 project.

The notebooks document the data, models, scoring logic, comparisons, ticket-pack construction, backtesting, and model limitations using readable explanations, tables, and charts.

## Start

From the project root:

```powershell
python -m pip install -r requirements-notebooks.txt
jupyter notebook
```

The notebooks can also be opened directly in VS Code.

## Recommended order

1. `00_project_overview.ipynb`
2. `01_data_overview_and_quality.ipynb`
3. `02_frequency_model.ipynb`
4. `03_gap_model.ipynb`
5. `04_pattern_balance_model.ipynb`
6. `05_combined_strategy.ipynb`
7. `06_ml_extensions.ipynb`
8. `07_model_comparison.ipynb`
9. `08_ensemble_and_weighting.ipynb`
10. `09_ticket_builder_and_portfolio.ipynb`
11. `10_backtest_and_performance.ipynb`
12. `11_explainability_and_conclusions.ipynb`

## Purpose

- Explain each model in plain language.
- Show the input datasets and generated reports.
- Visualize frequencies, gaps, patterns, scores, and performance history.
- Make the project easier to review and maintain.
- Keep model limitations clear.

## Important limitation

The notebooks are educational and analytical. They do not guarantee future lottery results.
