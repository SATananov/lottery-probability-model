# Gap / Interval Next-Draw Probability Model Report

## Purpose

This report estimates which numbers have the strongest next-draw score based on historical recurrence intervals.

## Model method

Ranks numbers by recurrence intervals. For each number, the model compares the current gap since its last appearance with its average historical interval, estimates an interval hazard probability, and combines it with the fair 6/49 baseline and empirical frequency.

## Important warning

The fair mathematical chance for any single number to appear in the next 6/49 draw is still 6/49. This model is a statistical training estimate based on historical intervals, not a guarantee.

## Training summary

- Training draws: 10010
- Baseline next-draw probability per number: 12.24%
- Recommended gap ticket: [14, 23, 34, 37, 42, 45]

## Top next-draw probability numbers

| Rank | Number | Combined probability | Baseline | Interval hazard | Empirical | Current gap | Avg interval | Gap ratio | Cases | Hits | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 45 | 15.83% | 12.24% | 14.73% | 12.35% | 19 | 8.07 | 2.48 | 93 | 14 | STRONGLY_OVERDUE |
| 2 | 34 | 15.71% | 12.24% | 14.21% | 12.89% | 17 | 7.74 | 2.32 | 125 | 18 | STRONGLY_OVERDUE |
| 3 | 23 | 14.79% | 12.24% | 12.70% | 11.67% | 16 | 8.56 | 1.99 | 157 | 20 | STRONGLY_OVERDUE |
| 4 | 42 | 14.47% | 12.24% | 11.72% | 12.30% | 18 | 8.12 | 2.34 | 120 | 14 | STRONGLY_OVERDUE |
| 5 | 37 | 14.45% | 12.24% | 11.54% | 12.62% | 17 | 7.91 | 2.27 | 122 | 14 | STRONGLY_OVERDUE |
| 6 | 14 | 14.44% | 12.24% | 15.01% | 12.04% | 10 | 8.30 | 1.33 | 331 | 50 | OVERDUE |
| 7 | 4 | 13.97% | 12.24% | 10.49% | 12.58% | 16 | 7.93 | 2.14 | 145 | 15 | STRONGLY_OVERDUE |
| 8 | 1 | 13.86% | 12.24% | 11.59% | 12.41% | 12 | 8.05 | 1.62 | 251 | 29 | OVERDUE |
| 9 | 43 | 13.81% | 12.24% | 11.74% | 12.19% | 12 | 8.18 | 1.59 | 256 | 30 | OVERDUE |
| 10 | 33 | 13.76% | 12.24% | 12.57% | 12.11% | 11 | 8.25 | 1.45 | 286 | 36 | OVERDUE |
| 11 | 19 | 13.67% | 12.24% | 15.21% | 11.77% | 8 | 8.49 | 1.06 | 425 | 65 | NORMAL_INTERVAL |
| 12 | 12 | 13.16% | 12.24% | 10.07% | 12.39% | 12 | 8.07 | 1.61 | 241 | 24 | OVERDUE |
| 13 | 47 | 13.12% | 12.24% | 11.27% | 12.03% | 11 | 8.31 | 1.44 | 276 | 31 | OVERDUE |
| 14 | 30 | 12.83% | 12.24% | 14.42% | 12.34% | 6 | 8.10 | 0.86 | 546 | 79 | NORMAL_INTERVAL |
| 15 | 41 | 12.66% | 12.24% | 13.06% | 11.68% | 8 | 8.56 | 1.05 | 428 | 56 | NORMAL_INTERVAL |
| 16 | 27 | 12.49% | 12.24% | 11.52% | 12.02% | 9 | 8.32 | 1.20 | 374 | 43 | NORMAL_INTERVAL |
| 17 | 13 | 11.97% | 12.24% | 12.75% | 12.10% | 6 | 8.27 | 0.85 | 572 | 73 | NORMAL_INTERVAL |
| 18 | 9 | 11.79% | 12.24% | 12.02% | 12.44% | 6 | 8.03 | 0.87 | 566 | 68 | NORMAL_INTERVAL |
| 19 | 17 | 11.75% | 12.24% | 5.58% | 12.52% | 18 | 7.97 | 2.38 | 104 | 5 | STRONGLY_OVERDUE |
| 20 | 6 | 11.75% | 12.24% | 12.59% | 12.66% | 5 | 7.90 | 0.76 | 651 | 82 | NORMAL_INTERVAL |

## Interpretation

A high combined probability means that the number is interesting according to its historical interval rhythm. It does not mean the number is guaranteed to appear in the next draw.
