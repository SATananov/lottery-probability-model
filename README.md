# Lottery Probability Simulator 6/49

This is a Python training project for mathematical probability, historical draw analysis, transparent statistical scoring models, and backtesting.

## Important note

This project does not guarantee or truly predict winning lottery numbers.

A fair 6/49 lottery should be treated as random. Historical statistics can show that some numbers appeared more often, less often, close to average, or after certain intervals, but that does not prove they will behave the same way in the future.

The correct workflow is:

```text
official historical data -> validation -> training -> backtesting -> comparison with random baseline
```

## Main methods

1. **Exact probability model**  
   Calculates the true mathematical 6/49 probabilities using combinations and the hypergeometric distribution.

2. **Monte Carlo simulation**  
   Simulates many random lottery draws and compares match counts.

3. **Historical analysis**  
   Reads `data/historical_draws.csv` and reports frequency, overdue numbers, pairs, even/odd balance, low/high balance, and sum statistics.

4. **Hot / Frequency model**  
   Scores numbers that have appeared more often in the historical data.

5. **Cold / Underrepresented model**  
   Scores numbers that appeared less often than expected and have larger gaps.

6. **Middle / Balanced model**  
   Scores numbers closest to the expected fair 6/49 behavior.

7. **Gap / Interval model**  
   Scores numbers according to historical recurrence intervals and estimated next-draw interval probability.

8. **Combined strategy model**  
   Combines hot, cold, middle, gap, pair/co-occurrence, rolling-window, and structure scores. It produces model confidence and relative ranking, not guaranteed winning numbers.

## Official BST data import

The project includes an importer for official Bulgarian Sports Totalizator 6/49 archive data.

Run:

```bash
python scripts/download_bst_649_history.py
```

The importer writes:

```text
data/historical_draws.csv
reports/data_import_report.md
```

Then train all models:

```bash
python train_model.py
python train_cold_model.py
python train_middle_model.py
python train_gap_model.py
python train_combined_model.py
python app.py
```

## Project structure

```text
lottery-probability-model/
в”њв”Ђв”Ђ app.py
в”њв”Ђв”Ђ train_model.py
в”њв”Ђв”Ђ train_cold_model.py
в”њв”Ђв”Ђ train_middle_model.py
в”њв”Ђв”Ђ train_gap_model.py
в”њв”Ђв”Ђ train_combined_model.py
в”њв”Ђв”Ђ README.md
в”њв”Ђв”Ђ data/
в”‚   в”њв”Ђв”Ђ DATA_SOURCE_NOTES.md
в”‚   в”њв”Ђв”Ђ historical_draws.csv
в”‚   в””в”Ђв”Ђ raw/
в”‚       в””в”Ђв”Ђ bst_649_yearly/
в”њв”Ђв”Ђ models/
в”‚   в”њв”Ђв”Ђ lottery_frequency_model.json
в”‚   в”њв”Ђв”Ђ lottery_cold_model.json
в”‚   в”њв”Ђв”Ђ lottery_middle_model.json
в”‚   в”њв”Ђв”Ђ lottery_gap_model.json
в”‚   в””в”Ђв”Ђ lottery_combined_model.json
в”њв”Ђв”Ђ reports/
в”‚   в”њв”Ђв”Ђ data_import_report.md
в”‚   в”њв”Ђв”Ђ historical_report.md
в”‚   в”њв”Ђв”Ђ frequency_model_report.md
в”‚   в”њв”Ђв”Ђ cold_model_report.md
в”‚   в”њв”Ђв”Ђ middle_model_report.md
в”‚   в”њв”Ђв”Ђ gap_model_report.md
в”‚   в”њв”Ђв”Ђ combined_strategy_report.md
в”‚   в””в”Ђв”Ђ combined_backtest_report.md
в”њв”Ђв”Ђ scripts/
в”‚   в””в”Ђв”Ђ download_bst_649_history.py
в””в”Ђв”Ђ src/
    в”њв”Ђв”Ђ data_importer.py
    в”њв”Ђв”Ђ probability.py
    в”њв”Ђв”Ђ generator.py
    в”њв”Ђв”Ђ simulation.py
    в”њв”Ђв”Ђ historical_analysis.py
    в”њв”Ђв”Ђ frequency_model.py
    в”њв”Ђв”Ђ cold_number_model.py
    в”њв”Ђв”Ђ middle_number_model.py
    в”њв”Ђв”Ђ gap_interval_model.py
    в”њв”Ђв”Ђ combination_filters.py
    в”њв”Ђв”Ђ pair_model.py
    в”њв”Ђв”Ђ rolling_window_model.py
    в”њв”Ђв”Ђ combined_strategy_model.py
    в””в”Ђв”Ђ backtesting.py
```

## Interpretation

The theoretical chance of one exact 6-number ticket remains:

```text
1 in 13,983,816
```

Model confidence and relative probability are only statistical ranking scores within the generated candidate combinations.
