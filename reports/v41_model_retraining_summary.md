# v41 Model Retraining Summary

Status: v41 model retraining completed on canonical draw events.

## Dataset

- Canonical dataset: `data\v41_canonical_draw_events.csv`
- Total draw events: 10064
- Train events: 8051
- Test events: 2013
- Uses drawing_no: True
- Bonus model trained: False

## Models

- Frequency baseline
- Recency 250-event baseline
- SGD per-number classifier

## Metrics

### frequency_baseline

- Average hits top 6: 0.7099
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 896, '1': 835, '2': 253, '3': 28, '4': 1}
- Events with 3+ hits: 29
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

### recency_250_baseline

- Average hits top 6: 0.7481
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 866, '1': 825, '2': 286, '3': 35, '4': 1}
- Events with 3+ hits: 36
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

### sgd_number_classifier

- Average hits top 6: 0.7779
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 854, '1': 809, '2': 299, '3': 45, '4': 6}
- Events with 3+ hits: 51
- Events with 4+ hits: 6
- Events with 5+ hits: 0
- Events with 6 hits: 0

## Important warning

Lottery draws are random. These models produce ranking scores and diagnostics, not guaranteed winning numbers.

Bonus-number modeling is intentionally blocked because bonus-number data is not available in the canonical dataset.
