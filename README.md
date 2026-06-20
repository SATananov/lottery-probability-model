# Lottery Probability Simulator 6/49

This is a Python training project for mathematical probability, official historical draw analysis, transparent statistical models, simulations, and backtesting for Bulgarian Toto 2 - 6/49.

## Important note

This project does not guarantee winning lottery numbers.

A fair 6/49 lottery should be treated as random. Historical statistics can show frequency, gaps, balance, pairs, and model ranking signals, but they do not prove future draws are predictable.

The correct interpretation is:

```text
official historical data -> validation -> model training -> backtesting -> comparison with random baseline
```

## Main features

- exact 6/49 mathematical probability calculation;
- Monte Carlo simulation;
- official historical dataset import and audit;
- hot / frequency model;
- cold / underrepresented model;
- middle / balanced model;
- gap / interval model;
- advanced ensemble model;
- final combined strategy model;
- visual Streamlit app with Bulgarian UI support;
- manual draw upload and model refresh workflow.

## Run the visual app

```bash
python -m streamlit run streamlit_app.py
```

## Run the console workflow

```bash
python app.py
```

## Import official BST data

```bash
python scripts/download_bst_649_history.py
```

The importer writes:

```text
data/historical_draws.csv
reports/data_import_report.md
```

## Train all models

```bash
python train_model.py
python train_cold_model.py
python train_middle_model.py
python train_gap_model.py
python train_combined_model.py
python train_advanced_model.py
```

## Useful checks

```bash
python audit_dataset.py
python show_advanced_recommendations.py
python run_advanced_backtest.py
```

## Project structure

```text
lottery-probability-model/
├── app.py
├── streamlit_app.py
├── train_model.py
├── train_cold_model.py
├── train_middle_model.py
├── train_gap_model.py
├── train_combined_model.py
├── train_advanced_model.py
├── data/
│   ├── DATA_SOURCE_NOTES.md
│   ├── historical_draws.csv
│   └── raw/bst_649_yearly/
├── models/
│   ├── lottery_frequency_model.json
│   ├── lottery_cold_model.json
│   ├── lottery_middle_model.json
│   ├── lottery_gap_model.json
│   ├── lottery_combined_model.json
│   └── lottery_advanced_ensemble_model.json
├── reports/
├── scripts/
└── src/
```

## Interpretation

The theoretical chance of one exact 6-number ticket remains:

```text
1 in 13,983,816
```

Model confidence and relative probability are only statistical ranking scores inside the generated candidate combinations. They are not a real jackpot guarantee.
