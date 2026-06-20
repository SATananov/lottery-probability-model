# Gap / Interval Next-Draw Probability Model Report

## Purpose

This report estimates which numbers have the strongest next-draw score based on historical recurrence intervals.

## Model method

Ranks numbers by recurrence intervals. For each number, the model compares the current gap since its last appearance with its average historical interval, estimates an interval hazard probability, and combines it with the fair 6/49 baseline and empirical frequency.

## Important warning

The fair mathematical chance for any single number to appear in the next 6/49 draw is still 6/49. This model is a statistical training estimate based on historical intervals, not a guarantee.

## Training summary

- Training draws: 10009
- Baseline next-draw probability per number: 12.24%
- Recommended gap ticket: [14, 23, 34, 37, 42, 45]

## Top next-draw probability numbers

| Rank | Number | Combined probability | Baseline | Interval hazard | Empirical | Current gap | Avg interval | Gap ratio | Cases | Hits | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 34 | 15.99% | 12.24% | 14.83% | 12.88% | 17 | 7.75 | 2.32 | 126 | 19 | STRONGLY_OVERDUE |
| 2 | 45 | 15.83% | 12.24% | 14.73% | 12.33% | 19 | 8.08 | 2.47 | 93 | 14 | STRONGLY_OVERDUE |
| 3 | 37 | 15.04% | 12.24% | 12.85% | 12.63% | 17 | 7.91 | 2.28 | 124 | 16 | STRONGLY_OVERDUE |
| 4 | 23 | 14.74% | 12.24% | 12.63% | 11.60% | 16 | 8.61 | 1.97 | 158 | 20 | STRONGLY_OVERDUE |
| 5 | 14 | 14.45% | 12.24% | 15.05% | 12.02% | 10 | 8.31 | 1.32 | 330 | 50 | OVERDUE |
| 6 | 42 | 14.42% | 12.24% | 11.63% | 12.25% | 18 | 8.16 | 2.33 | 121 | 14 | STRONGLY_OVERDUE |
| 7 | 4 | 13.99% | 12.24% | 10.49% | 12.70% | 16 | 7.85 | 2.17 | 145 | 15 | STRONGLY_OVERDUE |
| 8 | 1 | 13.85% | 12.24% | 11.54% | 12.42% | 12 | 8.04 | 1.62 | 252 | 29 | OVERDUE |
| 9 | 33 | 13.82% | 12.24% | 12.62% | 12.19% | 11 | 8.20 | 1.46 | 285 | 36 | OVERDUE |
| 10 | 19 | 13.52% | 12.24% | 14.82% | 11.83% | 8 | 8.45 | 1.07 | 423 | 63 | NORMAL_INTERVAL |
| 11 | 43 | 13.44% | 12.24% | 10.96% | 12.16% | 12 | 8.20 | 1.59 | 257 | 28 | OVERDUE |
| 12 | 12 | 13.20% | 12.24% | 10.11% | 12.41% | 12 | 8.05 | 1.61 | 240 | 24 | OVERDUE |
| 13 | 30 | 12.99% | 12.24% | 14.75% | 12.38% | 6 | 8.07 | 0.87 | 547 | 81 | NORMAL_INTERVAL |
| 14 | 47 | 12.94% | 12.24% | 10.77% | 12.10% | 11 | 8.26 | 1.45 | 271 | 29 | OVERDUE |
| 15 | 41 | 12.67% | 12.24% | 13.09% | 11.68% | 8 | 8.56 | 1.05 | 427 | 56 | NORMAL_INTERVAL |
| 16 | 27 | 12.32% | 12.24% | 11.23% | 11.94% | 9 | 8.37 | 1.19 | 375 | 42 | NORMAL_INTERVAL |
| 17 | 13 | 12.06% | 12.24% | 12.99% | 12.04% | 6 | 8.31 | 0.84 | 569 | 74 | NORMAL_INTERVAL |
| 18 | 9 | 11.84% | 12.24% | 12.13% | 12.45% | 6 | 8.03 | 0.87 | 569 | 69 | NORMAL_INTERVAL |
| 19 | 17 | 11.79% | 12.24% | 5.63% | 12.60% | 18 | 7.92 | 2.40 | 103 | 5 | STRONGLY_OVERDUE |
| 20 | 6 | 11.57% | 12.24% | 12.19% | 12.67% | 5 | 7.89 | 0.76 | 648 | 79 | NORMAL_INTERVAL |

## Interpretation

A high combined probability means that the number is interesting according to its historical interval rhythm. It does not mean the number is guaranteed to appear in the next draw.
