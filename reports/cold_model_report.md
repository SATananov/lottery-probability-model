# Cold Numbers Model Report

## Purpose

This report ranks lottery numbers that are underrepresented in the historical data. The model is useful for training and analysis, but it does not guarantee future lottery results.

## Model method

Ranks numbers that are historically below expected frequency, have larger recency gaps, and are cold in the recent window.

## Training summary

- Training draws: 10057
- Последен прозорец: 20
- Recommended cold ticket: [4, 12, 25, 34, 41, 44]

## Weights

- Deficit weight: 0.5
- Gap weight: 0.3
- Recent cold weight: 0.2

## Top underrepresented numbers

| Rank | Number | Cold score | Times drawn | Empirical probability | Expected probability | Deficit | Recent count | Recency gap | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 34 | 0.5000 | 1291 | 12.84% | 12.24% | -0.59% | 0 | 28 | OVER_EXPECTED |
| 2 | 44 | 0.4893 | 1290 | 12.83% | 12.24% | -0.58% | 0 | 27 | OVER_EXPECTED |
| 3 | 25 | 0.4464 | 1240 | 12.33% | 12.24% | -0.08% | 0 | 23 | OVER_EXPECTED |
| 4 | 12 | 0.4250 | 1249 | 12.42% | 12.24% | -0.17% | 0 | 21 | OVER_EXPECTED |
| 5 | 41 | 0.3242 | 1173 | 11.66% | 12.24% | 0.58% | 1 | 17 | UNDER_EXPECTED |
| 6 | 4 | 0.3219 | 1276 | 12.69% | 12.24% | -0.44% | 1 | 19 | OVER_EXPECTED |
| 7 | 21 | 0.3112 | 1289 | 12.82% | 12.24% | -0.57% | 1 | 18 | OVER_EXPECTED |
| 8 | 48 | 0.3112 | 1269 | 12.62% | 12.24% | -0.37% | 1 | 18 | OVER_EXPECTED |
| 9 | 47 | 0.3076 | 1214 | 12.07% | 12.24% | 0.17% | 1 | 17 | UNDER_EXPECTED |
| 10 | 31 | 0.2468 | 1179 | 11.72% | 12.24% | 0.52% | 1 | 10 | UNDER_EXPECTED |
| 11 | 24 | 0.2362 | 1240 | 12.33% | 12.24% | -0.08% | 1 | 11 | OVER_EXPECTED |
| 12 | 32 | 0.2259 | 1204 | 11.97% | 12.24% | 0.27% | 1 | 9 | UNDER_EXPECTED |
| 13 | 33 | 0.2059 | 1227 | 12.20% | 12.24% | 0.04% | 1 | 8 | UNDER_EXPECTED |
| 14 | 18 | 0.2011 | 1196 | 11.89% | 12.24% | 0.35% | 2 | 14 | UNDER_EXPECTED |
| 15 | 6 | 0.1826 | 1272 | 12.65% | 12.24% | -0.40% | 1 | 6 | OVER_EXPECTED |
| 16 | 20 | 0.1695 | 1221 | 12.14% | 12.24% | 0.10% | 2 | 12 | UNDER_EXPECTED |
| 17 | 27 | 0.1677 | 1199 | 11.92% | 12.24% | 0.32% | 2 | 11 | UNDER_EXPECTED |
| 18 | 10 | 0.1521 | 1201 | 11.94% | 12.24% | 0.30% | 1 | 2 | UNDER_EXPECTED |
| 19 | 23 | 0.1432 | 1169 | 11.62% | 12.24% | 0.62% | 3 | 11 | UNDER_EXPECTED |
| 20 | 3 | 0.1425 | 1182 | 11.75% | 12.24% | 0.49% | 2 | 8 | UNDER_EXPECTED |

## Interpretation

A high cold score means a number is below expected frequency, has not appeared recently, or both. This is not proof that the number is due to appear. It is only a transparent statistical score.
