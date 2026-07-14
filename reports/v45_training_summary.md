# v45 Prediction Engine Pro Training Summary

Status: v45 training pipeline completed.

## Safety note

Lottery draws are random. These outputs are statistical rankings and rule-aware ticket suggestions, not guaranteed winning numbers.

## Dataset

- Source: `data\v41_canonical_draw_events.csv`
- Valid draw events: 10064
- Years: 1958–2026
- Train events: 8051
- Test events: 2013
- Bonus numbers used: False

## Best historical-check model

- Model: `sgd_logistic_probability`
- Average hits in top 6: 0.7740
- Max hits in top 6: 4

## Current primary rule-aware suggestion

- Numbers: **2 11 37 42 48 49**

## Models compared

- `frequency_baseline`: avg=0.7099, max=4, 3+ events=29
- `recency_250_baseline`: avg=0.7481, max=4, 3+ events=36
- `gap_rhythm_statistical`: avg=0.7024, max=4, 3+ events=35
- `random_baseline`: avg=0.7268, max=4, 3+ events=38
- `sgd_logistic_probability`: avg=0.7740, max=4, 3+ events=35
- `gaussian_naive_bayes`: avg=0.7357, max=4, 3+ events=42
- `v45_pro_ensemble`: avg=0.7690, max=4, 3+ events=38

## Output files

- `models\v45\v45_latest_number_scores.json`
- `models\v45\v45_final_prediction_tickets.json`
- `models\v45\v45_model_metadata.json`
- `reports\v45_backtest_results.csv`
- `reports\v45_backtest_by_model.csv`
- `reports\v45_feature_importance.csv`
