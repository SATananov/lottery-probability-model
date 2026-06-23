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
- разширен обединен модел model;
- final combined strategy model;
- visual Streamlit app with Bulgarian UI support;
- manual draw upload and model refresh flow.

## Run the visual app

```bash
python -m streamlit run streamlit_app.py
```

## Run the console update flow

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

## МЛ разширения — класификация, клъстеризация и 2D карта

Проектът вече включва допълнителен образователен ML слой:

- **Feature Engineering** — извличане на характеристики от всяка комбинация: честота, интервал, баланс, двойки, тройки, структура и риск от човешки шаблон.
- **Класификация** — класифицира фишовете като слаб, нормален или силен статистически фиш.
- **Клъстеризация** — групира комбинациите по статистически профил.
- **Редукция на размерността** — прави 2D карта на комбинациите чрез PCA from scratch.
- **МЛ инструменти** — добавени са конфигурация, карта на модела, версиониран модел и отделни отчети.
- **Историческа проверка** — има допълнителна историческа проверка на МЛ разширенията.

Важно: тези методи **не променят реалния шанс** за точна комбинация 6/49. Те са статистически анализ и визуално сравнение, не гарантирано предсказване.

Стартиране на МЛ разширенията от терминал:

```powershell
python train_ml_extensions.py
```

Streamlit приложението има страница **МЛ лаборатория**, където можеш да видиш препоръки, класификация, клъстери, 2D карта и отчетите.

## Прогноза / Prediction Engine v36

Проектът включва страница **Прогноза**, която генерира статистическа прогноза за следващ неизвестен тираж. Тя използва всички налични модели и историческата проверка, но не променя реалния шанс за печалба.

Команда:

```powershell
python predict_next_draw.py
```

Изходни файлове:

- `models/lottery_prediction_model.json`
- `reports/prediction_report.md`
- `reports/prediction_model_card.md`
- `reports/prediction_methodology_report.md`
