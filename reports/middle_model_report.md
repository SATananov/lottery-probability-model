# Middle / Balanced Numbers Model Report

## Purpose

This report ranks numbers that are closest to the expected fair 6/49 behavior. The model avoids extreme hot and cold numbers.

## Model method

Ranks numbers whose historical frequency, recent frequency, and recency gap are closest to the expected fair 6/49 behavior.

## Training summary

- Training draws: 10057
- Последен прозорец: 20
- Recommended middle ticket: [3, 5, 19, 36, 45, 46]

## Weights

- Closeness to expected frequency: 0.6
- Gap balance: 0.25
- Recent balance: 0.15

## Top balanced numbers

| Rank | Number | Middle score | Times drawn | Empirical probability | Expected probability | Difference | Z-score | Gap | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 45 | 0.9635 | 1238 | 12.31% | 12.24% | 0.06% | 0.20 | 7 | MIDDLE |
| 2 | 46 | 0.9596 | 1246 | 12.39% | 12.24% | 0.14% | 0.44 | 7 | MIDDLE |
| 3 | 36 | 0.9321 | 1221 | 12.14% | 12.24% | -0.10% | -0.32 | 8 | MIDDLE |
| 4 | 3 | 0.9193 | 1182 | 11.75% | 12.24% | -0.49% | -1.50 | 8 | BELOW_MIDDLE |
| 5 | 19 | 0.9111 | 1189 | 11.82% | 12.24% | -0.42% | -1.29 | 6 | BELOW_MIDDLE |
| 6 | 5 | 0.9025 | 1219 | 12.12% | 12.24% | -0.12% | -0.38 | 9 | MIDDLE |
| 7 | 33 | 0.8800 | 1227 | 12.20% | 12.24% | -0.04% | -0.14 | 8 | MIDDLE |
| 8 | 35 | 0.8564 | 1243 | 12.36% | 12.24% | 0.11% | 0.35 | 4 | MIDDLE |
| 9 | 6 | 0.8508 | 1272 | 12.65% | 12.24% | 0.40% | 1.23 | 6 | ABOVE_MIDDLE |
| 10 | 38 | 0.8440 | 1231 | 12.24% | 12.24% | -0.00% | -0.01 | 7 | MIDDLE |
| 11 | 17 | 0.8385 | 1267 | 12.60% | 12.24% | 0.35% | 1.08 | 4 | ABOVE_MIDDLE |
| 12 | 32 | 0.8339 | 1204 | 11.97% | 12.24% | -0.27% | -0.84 | 9 | MIDDLE |
| 13 | 27 | 0.8230 | 1199 | 11.92% | 12.24% | -0.32% | -0.99 | 11 | MIDDLE |
| 14 | 43 | 0.8163 | 1222 | 12.15% | 12.24% | -0.09% | -0.29 | 3 | MIDDLE |
| 15 | 30 | 0.8138 | 1246 | 12.39% | 12.24% | 0.14% | 0.44 | 3 | MIDDLE |
| 16 | 39 | 0.8104 | 1210 | 12.03% | 12.24% | -0.21% | -0.65 | 3 | MIDDLE |
| 17 | 2 | 0.8047 | 1222 | 12.15% | 12.24% | -0.09% | -0.29 | 6 | MIDDLE |
| 18 | 23 | 0.8021 | 1169 | 11.62% | 12.24% | -0.62% | -1.90 | 11 | BELOW_MIDDLE |
| 19 | 20 | 0.7988 | 1221 | 12.14% | 12.24% | -0.10% | -0.32 | 12 | MIDDLE |
| 20 | 15 | 0.7872 | 1221 | 12.14% | 12.24% | -0.10% | -0.32 | 2 | MIDDLE |

## Interpretation

A high middle score means a number is close to the expected average statistical behavior. This is not proof that the number will appear next; it is only a transparent balancing strategy.
