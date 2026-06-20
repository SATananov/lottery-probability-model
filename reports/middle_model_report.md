# Middle / Balanced Numbers Model Report

## Purpose

This report ranks numbers that are closest to the expected fair 6/49 behavior. The model avoids extreme hot and cold numbers.

## Model method

Ranks numbers whose historical frequency, recent frequency, and recency gap are closest to the expected fair 6/49 behavior.

## Training summary

- Training draws: 10009
- Recent window: 20
- Recommended middle ticket: [6, 9, 10, 19, 30, 36]

## Weights

- Closeness to expected frequency: 0.6
- Gap balance: 0.25
- Recent balance: 0.15

## Top balanced numbers

| Rank | Number | Middle score | Times drawn | Empirical probability | Expected probability | Difference | Z-score | Gap | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 36 | 0.9533 | 1211 | 12.10% | 12.24% | -0.15% | -0.44 | 7 | MIDDLE |
| 2 | 9 | 0.9218 | 1246 | 12.45% | 12.24% | 0.20% | 0.62 | 6 | MIDDLE |
| 3 | 30 | 0.9190 | 1239 | 12.38% | 12.24% | 0.13% | 0.41 | 6 | MIDDLE |
| 4 | 10 | 0.9116 | 1197 | 11.96% | 12.24% | -0.29% | -0.87 | 6 | MIDDLE |
| 5 | 6 | 0.8699 | 1268 | 12.67% | 12.24% | 0.42% | 1.29 | 5 | ABOVE_MIDDLE |
| 6 | 19 | 0.8618 | 1184 | 11.83% | 12.24% | -0.42% | -1.27 | 8 | BELOW_MIDDLE |
| 7 | 13 | 0.8605 | 1205 | 12.04% | 12.24% | -0.21% | -0.63 | 6 | MIDDLE |
| 8 | 14 | 0.8564 | 1203 | 12.02% | 12.24% | -0.23% | -0.69 | 10 | MIDDLE |
| 9 | 41 | 0.8545 | 1169 | 11.68% | 12.24% | -0.57% | -1.73 | 8 | BELOW_MIDDLE |
| 10 | 38 | 0.8540 | 1222 | 12.21% | 12.24% | -0.04% | -0.11 | 4 | MIDDLE |
| 11 | 33 | 0.8298 | 1220 | 12.19% | 12.24% | -0.06% | -0.17 | 11 | MIDDLE |
| 12 | 8 | 0.8286 | 1240 | 12.39% | 12.24% | 0.14% | 0.44 | 5 | MIDDLE |
| 13 | 39 | 0.8256 | 1205 | 12.04% | 12.24% | -0.21% | -0.63 | 5 | MIDDLE |
| 14 | 29 | 0.8080 | 1252 | 12.51% | 12.24% | 0.26% | 0.81 | 3 | MIDDLE |
| 15 | 16 | 0.8064 | 1196 | 11.95% | 12.24% | -0.30% | -0.90 | 3 | MIDDLE |
| 16 | 12 | 0.7959 | 1242 | 12.41% | 12.24% | 0.16% | 0.50 | 12 | MIDDLE |
| 17 | 15 | 0.7818 | 1217 | 12.16% | 12.24% | -0.09% | -0.26 | 2 | MIDDLE |
| 18 | 11 | 0.7810 | 1266 | 12.65% | 12.24% | 0.40% | 1.23 | 4 | ABOVE_MIDDLE |
| 19 | 44 | 0.7717 | 1285 | 12.84% | 12.24% | 0.59% | 1.81 | 4 | ABOVE_MIDDLE |
| 20 | 27 | 0.7711 | 1195 | 11.94% | 12.24% | -0.31% | -0.93 | 9 | MIDDLE |

## Interpretation

A high middle score means a number is close to the expected average statistical behavior. This is not proof that the number will appear next; it is only a transparent balancing strategy.
