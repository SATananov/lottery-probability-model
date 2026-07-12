# Отчет от историческа проверка

## Goal

This report checks whether the historical frequency model performs better than a random baseline on later draws.

## Summary

- Проверени тиражи: 10047
- Минимален обучаващ период: 10
- Последен прозорец: 20
- Случайно семе: 42
- Model average matches: 0.7343
- Random average matches: 0.7144

## Conclusion

The frequency model performed better than the random baseline in this run. The sample is larger, but lottery results should still be treated as random unless a strong, stable signal is proven.

## Match distribution

| Matches | Model count | Random count |
|---:|---:|---:|
| 0 | 4369 | 4487 |
| 1 | 4161 | 4116 |
| 2 | 1340 | 1275 |
| 3 | 171 | 164 |
| 4 | 6 | 5 |
| 5 | 0 | 0 |
| 6 | 0 | 0 |

## Tested draw detail

The complete row-level table is intentionally not stored in Markdown. It is reproducible by rerunning the corresponding backtest script; only a small head/tail sample is retained here for review.

| Draw ID | Date | Actual numbers | Model ticket | Model matches | Random ticket | Random matches |
|:---|:---|:---|:---|---:|:---|---:|
| 11 |  | [7, 8, 11, 19, 29, 30] | [8, 10, 18, 22, 38, 49] | 1 | [2, 8, 15, 16, 18, 41] | 1 |
| 12 |  | [2, 16, 18, 27, 34, 47] | [8, 10, 18, 22, 38, 49] | 1 | [6, 7, 9, 35, 44, 48] | 0 |
| 13 |  | [9, 11, 21, 30, 33, 48] | [8, 10, 18, 22, 38, 49] | 0 | [2, 3, 6, 14, 28, 38] | 0 |
| … | … | … | … | … |
| 10055 | 2026-06-11 | [1, 10, 11, 15, 16, 37] | [2, 8, 13, 38, 42, 49] | 0 | [14, 18, 20, 34, 36, 45] | 0 |
| 10056 | 2026-06-14 | [1, 7, 8, 14, 29, 42] | [1, 2, 8, 38, 42, 49] | 3 | [9, 25, 26, 29, 37, 38] | 1 |
| 10057 | 2026-06-18 | [22, 26, 28, 29, 40, 42] | [1, 2, 8, 38, 42, 49] | 1 | [8, 16, 18, 25, 44, 45] | 0 |
