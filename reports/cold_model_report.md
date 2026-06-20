# Cold Numbers Model Report

## Purpose

This report ranks lottery numbers that are underrepresented in the historical data. The model is useful for training and analysis, but it does not guarantee future lottery results.

## Model method

Ranks numbers that are historically below expected frequency, have larger recency gaps, and are cold in the recent window.

## Training summary

- Training draws: 10009
- Recent window: 20
- Recommended cold ticket: [17, 23, 34, 37, 42, 45]

## Weights

- Deficit weight: 0.5
- Gap weight: 0.3
- Recent cold weight: 0.2

## Top underrepresented numbers

| Rank | Number | Cold score | Times drawn | Empirical probability | Expected probability | Deficit | Recent count | Recency gap | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 45 | 0.4183 | 1234 | 12.33% | 12.24% | -0.08% | 1 | 19 | OVER_EXPECTED |
| 2 | 17 | 0.4025 | 1261 | 12.60% | 12.24% | -0.35% | 1 | 18 | OVER_EXPECTED |
| 3 | 42 | 0.4025 | 1226 | 12.25% | 12.24% | -0.00% | 1 | 18 | OVER_EXPECTED |
| 4 | 23 | 0.3973 | 1161 | 11.60% | 12.24% | 0.65% | 1 | 16 | UNDER_EXPECTED |
| 5 | 34 | 0.3868 | 1289 | 12.88% | 12.24% | -0.63% | 1 | 17 | OVER_EXPECTED |
| 6 | 37 | 0.3868 | 1264 | 12.63% | 12.24% | -0.38% | 1 | 17 | OVER_EXPECTED |
| 7 | 4 | 0.3710 | 1271 | 12.70% | 12.24% | -0.45% | 1 | 16 | OVER_EXPECTED |
| 8 | 43 | 0.3113 | 1217 | 12.16% | 12.24% | 0.09% | 1 | 12 | UNDER_EXPECTED |
| 9 | 1 | 0.3078 | 1243 | 12.42% | 12.24% | -0.17% | 1 | 12 | OVER_EXPECTED |
| 10 | 47 | 0.2980 | 1211 | 12.10% | 12.24% | 0.15% | 1 | 11 | UNDER_EXPECTED |
| 11 | 41 | 0.2677 | 1169 | 11.68% | 12.24% | 0.57% | 1 | 8 | UNDER_EXPECTED |
| 12 | 19 | 0.2616 | 1184 | 11.83% | 12.24% | 0.42% | 1 | 8 | UNDER_EXPECTED |
| 13 | 12 | 0.2261 | 1242 | 12.41% | 12.24% | -0.16% | 2 | 12 | OVER_EXPECTED |
| 14 | 13 | 0.2215 | 1205 | 12.04% | 12.24% | 0.21% | 1 | 6 | UNDER_EXPECTED |
| 15 | 39 | 0.2057 | 1205 | 12.04% | 12.24% | 0.21% | 1 | 5 | UNDER_EXPECTED |
| 16 | 8 | 0.1973 | 1240 | 12.39% | 12.24% | -0.14% | 1 | 5 | OVER_EXPECTED |
| 17 | 11 | 0.1815 | 1266 | 12.65% | 12.24% | -0.40% | 1 | 4 | OVER_EXPECTED |
| 18 | 44 | 0.1815 | 1285 | 12.84% | 12.24% | -0.59% | 1 | 4 | OVER_EXPECTED |
| 19 | 33 | 0.1760 | 1220 | 12.19% | 12.24% | 0.06% | 3 | 11 | UNDER_EXPECTED |
| 20 | 14 | 0.1671 | 1203 | 12.02% | 12.24% | 0.23% | 3 | 10 | UNDER_EXPECTED |

## Interpretation

A high cold score means a number is below expected frequency, has not appeared recently, or both. This is not proof that the number is due to appear. It is only a transparent statistical score.
