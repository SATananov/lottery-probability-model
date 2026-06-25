# v41 Model Retraining Summary

Status: v41 model retraining completed on canonical draw events.

## Dataset

- Canonical dataset: `data\v41_canonical_draw_events.csv`
- Total draw events: 10058
- Train events: 8046
- Test events: 2012
- Uses drawing_no: True
- Bonus model trained: False

## Models

- Frequency baseline
- Recency 250-event baseline
- SGD per-number classifier

## Metrics

### frequency_baseline

- Average hits top 6: 0.7097
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 894, '1': 837, '2': 253, '3': 27, '4': 1}
- Events with 3+ hits: 28
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

### recency_250_baseline

- Average hits top 6: 0.7470
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 865, '1': 828, '2': 283, '3': 35, '4': 1}
- Events with 3+ hits: 36
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

### sgd_number_classifier

- Average hits top 6: 0.7416
- Median hits top 6: 1.0000
- Max hits top 6: 4
- Hit distribution: {'0': 878, '1': 814, '2': 283, '3': 36, '4': 1}
- Events with 3+ hits: 37
- Events with 4+ hits: 1
- Events with 5+ hits: 0
- Events with 6 hits: 0

## Important warning

Lottery draws are random. These models produce ranking scores and diagnostics, not guaranteed winning numbers.

Bonus-number modeling is intentionally blocked because bonus-number data is not available in the canonical dataset.
