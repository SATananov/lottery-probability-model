# v45 Prediction Engine Pro Training Summary

Status: v45 training pipeline completed.

## Safety note

Lottery draws are random. These outputs are statistical rankings and rule-aware ticket suggestions, not guaranteed winning numbers.

## Dataset

- Source: `data\v41_canonical_draw_events.csv`
- Valid draw events: 10060
- Years: 1958–2026
- Train events: 8048
- Test events: 2012
- Bonus numbers used: False

## Best historical-check model

- Model: `v45_pro_ensemble`
- Average hits in top 6: 0.7619
- Max hits in top 6: 4

## Current primary rule-aware suggestion

- Numbers: **11 17 22 43 44 48**

## Models compared

- `frequency_baseline`: avg=0.7097, max=4, 3+ events=28
- `recency_250_baseline`: avg=0.7475, max=4, 3+ events=36
- `gap_rhythm_statistical`: avg=0.6998, max=4, 3+ events=35
- `random_baseline`: avg=0.7256, max=4, 3+ events=38
- `sgd_logistic_probability`: avg=0.7580, max=4, 3+ events=41
- `gaussian_naive_bayes`: avg=0.7366, max=4, 3+ events=43
- `v45_pro_ensemble`: avg=0.7619, max=4, 3+ events=54

## Output files

- `models\v45\v45_latest_number_scores.json`
- `models\v45\v45_final_prediction_tickets.json`
- `models\v45\v45_model_metadata.json`
- `reports\v45_backtest_results.csv`
- `reports\v45_backtest_by_model.csv`
- `reports\v45_feature_importance.csv`
