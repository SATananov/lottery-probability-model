# v41 Model Retraining Summary

Status: v41 model retraining completed on canonical draw events.

## Dataset

- Canonical dataset: `data/v41_canonical_draw_events.csv`
- Total draw events: 10061
- Train events: 8048
- Test events: 2013
- Uses drawing_no: True
- Bonus model trained: False

## Models

- Frequency baseline
- Recency 250-event baseline
- SGD per-number classifier

## Metrics

### frequency_baseline

- Average hits top 6: 0.7094
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 895, '1': 837, '2': 253, '3': 27, '4': 1}
- Events with 3+ hits: 28
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

### recency_250_baseline

- Average hits top 6: 0.7481
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 865, '1': 827, '2': 285, '3': 35, '4': 1}
- Events with 3+ hits: 36
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

### sgd_number_classifier

- Average hits top 6: 0.7476
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 849, '1': 860, '2': 268, '3': 35, '4': 1}
- Events with 3+ hits: 36
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

## Important warning

Lottery draws are random. These models produce ranking scores and diagnostics, not guaranteed winning numbers.

Bonus-number modeling is intentionally blocked because bonus-number data is not available in the canonical dataset.
