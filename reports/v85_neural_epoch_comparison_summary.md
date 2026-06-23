# Step 85 — Neural Epoch Comparison Audit

**Status:** OK

This audit compares neural training checkpoints without replacing the active model automatically.

**Important:** Lottery outcomes are random. This is statistical analysis only, not a winning guarantee.

## Configuration

- Dataset: `data/v41_canonical_draw_events.csv`
- Valid draws: **10058**
- Train draws: **8046**
- Test draws: **2012**
- Train samples: **394254**
- Test samples: **98588**
- Hidden units: **18**
- Learning rate: **0.035**
- Epoch checkpoints: **90, 150, 300, 500**

## Results

| Epochs | Train loss | Test avg hits top 6 | Test max hits top 6 | Latest top 6 numbers |
|---:|---:|---:|---:|---|
| 90 | 0.694482 | 0.732604 | 4 | 6, 8, 4, 2, 14, 16 |
| 150 | 0.693828 | 0.723161 | 4 | 6, 8, 4, 2, 14, 28 |
| 300 | 0.693360 | 0.731113 | 4 | 28, 6, 26, 4, 8, 1 |
| 500 | 0.693249 | 0.721670 | 4 | 28, 26, 32, 1, 6, 30 |

## Best checkpoint

- Best by test average hits top 6: **90 epochs**
- Test avg hits top 6: **0.732604**
- Test max hits top 6: **4**

## Recommendation

Use this audit as evidence before changing the active neural configuration. Do not increase epochs only because training loss becomes lower; the test-period result matters more.
