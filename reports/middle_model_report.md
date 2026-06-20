# Middle / Balanced Numbers Model Report

## Purpose

This report ranks numbers that are closest to the expected fair 6/49 behavior. The model avoids extreme hot and cold numbers.

## Model method

Ranks numbers whose historical frequency, recent frequency, and recency gap are closest to the expected fair 6/49 behavior.

## Training summary

- Training draws: 10010
- Recent window: 20
- Recommended middle ticket: [6, 9, 10, 13, 30, 36]

## Weights

- Closeness to expected frequency: 0.6
- Gap balance: 0.25
- Recent balance: 0.15

## Top balanced numbers

| Rank | Number | Middle score | Times drawn | Empirical probability | Expected probability | Difference | Z-score | Gap | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 36 | 0.9527 | 1210 | 12.09% | 12.24% | -0.16% | -0.48 | 7 | MIDDLE |
| 2 | 9 | 0.9224 | 1245 | 12.44% | 12.24% | 0.19% | 0.59 | 6 | MIDDLE |
| 3 | 30 | 0.9210 | 1235 | 12.34% | 12.24% | 0.09% | 0.28 | 6 | MIDDLE |
| 4 | 10 | 0.9174 | 1209 | 12.08% | 12.24% | -0.17% | -0.51 | 6 | MIDDLE |
| 5 | 6 | 0.8705 | 1267 | 12.66% | 12.24% | 0.41% | 1.26 | 5 | ABOVE_MIDDLE |
| 6 | 13 | 0.8633 | 1211 | 12.10% | 12.24% | -0.15% | -0.45 | 6 | MIDDLE |
| 7 | 19 | 0.8588 | 1178 | 11.77% | 12.24% | -0.48% | -1.45 | 8 | BELOW_MIDDLE |
| 8 | 14 | 0.8573 | 1205 | 12.04% | 12.24% | -0.21% | -0.63 | 10 | MIDDLE |
| 9 | 41 | 0.8544 | 1169 | 11.68% | 12.24% | -0.57% | -1.73 | 8 | BELOW_MIDDLE |
| 10 | 38 | 0.8542 | 1229 | 12.28% | 12.24% | 0.03% | 0.10 | 4 | MIDDLE |
| 11 | 39 | 0.8280 | 1210 | 12.09% | 12.24% | -0.16% | -0.48 | 5 | MIDDLE |
| 12 | 33 | 0.8258 | 1212 | 12.11% | 12.24% | -0.14% | -0.42 | 11 | MIDDLE |
| 13 | 8 | 0.8248 | 1248 | 12.47% | 12.24% | 0.22% | 0.68 | 5 | MIDDLE |
| 14 | 29 | 0.8159 | 1236 | 12.35% | 12.24% | 0.10% | 0.31 | 3 | MIDDLE |
| 15 | 16 | 0.8029 | 1189 | 11.88% | 12.24% | -0.37% | -1.12 | 3 | BELOW_MIDDLE |
| 16 | 12 | 0.7969 | 1240 | 12.39% | 12.24% | 0.14% | 0.44 | 12 | MIDDLE |
| 17 | 15 | 0.7803 | 1214 | 12.13% | 12.24% | -0.12% | -0.36 | 2 | MIDDLE |
| 18 | 11 | 0.7781 | 1272 | 12.71% | 12.24% | 0.46% | 1.41 | 4 | ABOVE_MIDDLE |
| 19 | 27 | 0.7749 | 1203 | 12.02% | 12.24% | -0.23% | -0.69 | 9 | MIDDLE |
| 20 | 44 | 0.7718 | 1285 | 12.84% | 12.24% | 0.59% | 1.81 | 4 | ABOVE_MIDDLE |

## Interpretation

A high middle score means a number is close to the expected average statistical behavior. This is not proof that the number will appear next; it is only a transparent balancing strategy.
