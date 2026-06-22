# v41 Training Readiness Audit

Status: review required. No model retraining was performed.

## Summary

- Canonical dataset: `data\v41_canonical_draw_events.csv`
- Total draw events: 10058
- Total unique draws: 5176
- Years: 1958–2026 (69 years)
- Invalid number rows: 0
- Duplicate number rows: 0
- Duplicate keys: 0
- Date available rows: 49
- Date missing rows: 10009
- Bonus available rows: 0
- Bonus missing rows: 10058
- Draw groups with drawing_no=4: 15

## Drawing number counts

- drawing_no=1: 5176
- drawing_no=2: 3587
- drawing_no=3: 1280
- drawing_no=4: 15

## Drawings per draw distribution

- 1 drawing(s) per draw: 1589 draws
- 2 drawing(s) per draw: 2307 draws
- 3 drawing(s) per draw: 1265 draws
- 4 drawing(s) per draw: 15 draws

## Recommendation

- Use this canonical dataset for main-number v41 model retraining after review.
- Do not train a bonus-number model yet because bonus data is unavailable.
- Keep `drawing_no` as a rules-aware field.
- Do not merge several drawings into one 12/18/24-number record.
