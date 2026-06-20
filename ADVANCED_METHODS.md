# Advanced Methods and Backtesting

This project includes an advanced statistical layer for Bulgarian Toto 2 – 6/49.

Important: no method changes the true jackpot probability for one exact 6-number combination. The true odds remain 1 in 13,983,816. The advanced layer ranks combinations using statistical signals and validates those signals with rolling backtesting.

## Added methods

- Time-decay scoring: gives more weight to recent draws.
- Bayesian smoothing: reduces overreaction to random frequency noise.
- Chi-square fairness test: checks whether number frequencies look close to random expectation.
- Pair/triple significance: compares co-occurring pairs/triples against random expectation.
- Human-pattern avoidance: penalizes common human-selected patterns such as obvious sequences and all birthdate-range numbers.
- Portfolio optimizer: selects a diversified group of recommended tickets.
- Advanced ensemble model: combines all advanced signals into one main ranking score.
- Rolling backtesting engine: tests strategies on later draws using only earlier data.

## Commands

Train the advanced ensemble:

```powershell
python train_advanced_model.py
```

Run the backtesting engine:

```powershell
python run_advanced_backtest.py
```

Run the visual app:

```powershell
python -m streamlit run streamlit_app.py
```

## Outputs

- `models/lottery_advanced_ensemble_model.json`
- `models/lottery_advanced_backtest.json`
- `reports/advanced_ensemble_report.md`
- `reports/advanced_backtest_report.md`
