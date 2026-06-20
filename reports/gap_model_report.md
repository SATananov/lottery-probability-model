# Gap / Interval Next-Draw Probability Model Report

## Purpose

This report estimates which numbers have the strongest next-draw score based on historical recurrence intervals.

## Model method

Ranks numbers by recurrence intervals. For each number, the model compares the current gap since its last appearance with its average historical interval, estimates an interval hazard probability, and combines it with the fair 6/49 baseline and empirical frequency.

## Important warning

The fair mathematical chance for any single number to appear in the next 6/49 draw is still 6/49. This model is a statistical training estimate based on historical intervals, not a guarantee.

## Training summary

- Training draws: 10057
- Baseline next-draw probability per number: 12.24%
- Recommended gap ticket: [4, 18, 21, 24, 34, 48]

## Top next-draw probability numbers

| Rank | Number | Combined probability | Baseline | Interval hazard | Empirical | Current gap | Avg interval | Gap ratio | Cases | Hits | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 21 | 16.97% | 12.24% | 17.04% | 12.82% | 18 | 7.79 | 2.44 | 114 | 20 | STRONGLY_OVERDUE |
| 2 | 4 | 16.70% | 12.24% | 16.50% | 12.69% | 19 | 7.85 | 2.55 | 106 | 18 | STRONGLY_OVERDUE |
| 3 | 18 | 15.66% | 12.24% | 14.65% | 11.89% | 14 | 8.40 | 1.79 | 196 | 29 | STRONGLY_OVERDUE |
| 4 | 48 | 14.62% | 12.24% | 11.92% | 12.62% | 18 | 7.91 | 2.40 | 101 | 12 | STRONGLY_OVERDUE |
| 5 | 34 | 14.21% | 12.24% | 10.90% | 12.84% | 28 | 7.77 | 3.73 | 29 | 3 | STRONGLY_OVERDUE |
| 6 | 24 | 13.82% | 12.24% | 12.45% | 12.33% | 11 | 8.10 | 1.48 | 273 | 34 | OVERDUE |
| 7 | 41 | 13.53% | 12.24% | 9.92% | 11.66% | 17 | 8.56 | 2.10 | 144 | 14 | STRONGLY_OVERDUE |
| 8 | 20 | 13.19% | 12.24% | 10.44% | 12.14% | 12 | 8.22 | 1.58 | 251 | 26 | OVERDUE |
| 9 | 5 | 13.14% | 12.24% | 12.84% | 12.12% | 9 | 8.23 | 1.21 | 389 | 50 | NORMAL_INTERVAL |
| 10 | 27 | 13.12% | 12.24% | 11.40% | 11.92% | 11 | 8.38 | 1.43 | 299 | 34 | OVERDUE |
| 11 | 46 | 12.85% | 12.24% | 13.59% | 12.39% | 7 | 8.07 | 0.99 | 492 | 67 | NORMAL_INTERVAL |
| 12 | 36 | 12.85% | 12.24% | 12.98% | 12.14% | 8 | 8.22 | 1.09 | 446 | 58 | NORMAL_INTERVAL |
| 13 | 12 | 12.42% | 12.24% | 7.11% | 12.42% | 21 | 8.04 | 2.74 | 79 | 5 | STRONGLY_OVERDUE |
| 14 | 23 | 12.29% | 12.24% | 9.92% | 11.62% | 11 | 8.60 | 1.40 | 295 | 29 | OVERDUE |
| 15 | 38 | 12.18% | 12.24% | 12.24% | 12.24% | 7 | 8.17 | 0.98 | 490 | 60 | NORMAL_INTERVAL |
| 16 | 47 | 12.17% | 12.24% | 6.72% | 12.07% | 17 | 8.28 | 2.18 | 129 | 8 | STRONGLY_OVERDUE |
| 17 | 25 | 12.07% | 12.24% | 6.38% | 12.33% | 23 | 8.10 | 2.96 | 58 | 3 | STRONGLY_OVERDUE |
| 18 | 45 | 12.00% | 12.24% | 11.75% | 12.31% | 7 | 8.11 | 0.99 | 494 | 58 | NORMAL_INTERVAL |
| 19 | 44 | 11.95% | 12.24% | 5.88% | 12.83% | 27 | 7.78 | 3.60 | 30 | 1 | STRONGLY_OVERDUE |
| 20 | 33 | 11.93% | 12.24% | 10.88% | 12.20% | 8 | 8.19 | 1.10 | 415 | 45 | NORMAL_INTERVAL |

## Interpretation

A high combined probability means that the number is interesting according to its historical interval rhythm. It does not mean the number is guaranteed to appear in the next draw.
