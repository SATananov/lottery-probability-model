# Cold Numbers Model Report

## Purpose

This report ranks lottery numbers that are underrepresented in the historical data. The model is useful for training and analysis, but it does not guarantee future lottery results.

## Model method

Ranks numbers that are historically below expected frequency, have larger recency gaps, and are cold in the recent window.

## Training summary

- Training draws: 10010
- Recent window: 20
- Recommended cold ticket: [17, 23, 34, 37, 42, 45]

## Weights

- Deficit weight: 0.5
- Gap weight: 0.3
- Recent cold weight: 0.2

## Top underrepresented numbers

| Rank | Number | Cold score | Times drawn | Empirical probability | Expected probability | Deficit | Recent count | Recency gap | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 45 | 0.4183 | 1236 | 12.35% | 12.24% | -0.10% | 1 | 19 | OVER_EXPECTED |
| 2 | 17 | 0.4025 | 1253 | 12.52% | 12.24% | -0.27% | 1 | 18 | OVER_EXPECTED |
| 3 | 42 | 0.4025 | 1231 | 12.30% | 12.24% | -0.05% | 1 | 18 | OVER_EXPECTED |
| 4 | 23 | 0.3945 | 1168 | 11.67% | 12.24% | 0.58% | 1 | 16 | UNDER_EXPECTED |
| 5 | 34 | 0.3868 | 1290 | 12.89% | 12.24% | -0.64% | 1 | 17 | OVER_EXPECTED |
| 6 | 37 | 0.3868 | 1263 | 12.62% | 12.24% | -0.37% | 1 | 17 | OVER_EXPECTED |
| 7 | 4 | 0.3710 | 1259 | 12.58% | 12.24% | -0.33% | 1 | 16 | OVER_EXPECTED |
| 8 | 43 | 0.3101 | 1220 | 12.19% | 12.24% | 0.06% | 1 | 12 | UNDER_EXPECTED |
| 9 | 1 | 0.3078 | 1242 | 12.41% | 12.24% | -0.16% | 1 | 12 | OVER_EXPECTED |
| 10 | 47 | 0.3009 | 1204 | 12.03% | 12.24% | 0.22% | 1 | 11 | UNDER_EXPECTED |
| 11 | 41 | 0.2678 | 1169 | 11.68% | 12.24% | 0.57% | 1 | 8 | UNDER_EXPECTED |
| 12 | 19 | 0.2641 | 1178 | 11.77% | 12.24% | 0.48% | 1 | 8 | UNDER_EXPECTED |
| 13 | 12 | 0.2261 | 1240 | 12.39% | 12.24% | -0.14% | 2 | 12 | OVER_EXPECTED |
| 14 | 13 | 0.2191 | 1211 | 12.10% | 12.24% | 0.15% | 1 | 6 | UNDER_EXPECTED |
| 15 | 39 | 0.2037 | 1210 | 12.09% | 12.24% | 0.16% | 1 | 5 | UNDER_EXPECTED |
| 16 | 8 | 0.1973 | 1248 | 12.47% | 12.24% | -0.22% | 1 | 5 | OVER_EXPECTED |
| 17 | 11 | 0.1815 | 1272 | 12.71% | 12.24% | -0.46% | 1 | 4 | OVER_EXPECTED |
| 18 | 44 | 0.1815 | 1285 | 12.84% | 12.24% | -0.59% | 1 | 4 | OVER_EXPECTED |
| 19 | 33 | 0.1793 | 1212 | 12.11% | 12.24% | 0.14% | 3 | 11 | UNDER_EXPECTED |
| 20 | 14 | 0.1663 | 1205 | 12.04% | 12.24% | 0.21% | 3 | 10 | UNDER_EXPECTED |

## Interpretation

A high cold score means a number is below expected frequency, has not appeared recently, or both. This is not proof that the number is due to appear. It is only a transparent statistical score.
