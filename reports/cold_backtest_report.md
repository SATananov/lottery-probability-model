# Cold Numbers Отчет от историческа проверка

## Goal

This report tests whether choosing underrepresented numbers performs better than the hot frequency model or a random baseline.

## Summary

- Проверени тиражи: 10047
- Минимален обучаващ период: 10
- Последен прозорец: 20
- Случайно семе: 99
- Cold model average matches: 0.7163
- Hot frequency model average matches: 0.7343
- Random baseline average matches: 0.7289

## Conclusion

Best average in this run: hot frequency model. Cold=0.7163, Hot=0.7343, Random=0.7289. The sample is larger, but the result still needs cautious interpretation.

## Match distribution

| Matches | Cold count | Hot count | Random count |
|---:|---:|---:|---:|
| 0 | 4497 | 4369 | 4413 |
| 1 | 4079 | 4161 | 4128 |
| 2 | 1306 | 1340 | 1331 |
| 3 | 154 | 171 | 167 |
| 4 | 11 | 6 | 8 |
| 5 | 0 | 0 | 0 |
| 6 | 0 | 0 | 0 |

## Tested draw detail

The complete row-level table is intentionally not stored in Markdown. It is reproducible by rerunning the corresponding backtest script; only a small head/tail sample is retained here for review.

| Draw ID | Date | Actual numbers | Cold ticket | Cold matches | Hot ticket | Hot matches | Random ticket | Random matches |
|:---|:---|:---|:---|---:|:---|---:|:---|---:|
| 11 |  | [7, 8, 11, 19, 29, 30] | [3, 4, 5, 11, 16, 17] | 1 | [8, 10, 18, 22, 38, 49] | 1 | [12, 13, 15, 25, 26, 39] | 0 |
| 12 |  | [2, 16, 18, 27, 34, 47] | [3, 4, 5, 16, 17, 20] | 1 | [8, 10, 18, 22, 38, 49] | 1 | [6, 9, 16, 17, 25, 34] | 2 |
| 13 |  | [9, 11, 21, 30, 33, 48] | [3, 4, 5, 17, 20, 35] | 0 | [8, 10, 18, 22, 38, 49] | 0 | [6, 32, 35, 40, 44, 45] | 0 |
| … | … | … | … | … |
| 10055 | 2026-06-11 | [1, 10, 11, 15, 16, 37] | [10, 12, 22, 25, 34, 44] | 1 | [2, 8, 13, 38, 42, 49] | 0 | [10, 19, 21, 29, 41, 47] | 1 |
| 10056 | 2026-06-14 | [1, 7, 8, 14, 29, 42] | [12, 22, 25, 34, 40, 44] | 0 | [1, 2, 8, 38, 42, 49] | 3 | [10, 25, 27, 35, 41, 45] | 0 |
| 10057 | 2026-06-18 | [22, 26, 28, 29, 40, 42] | [12, 22, 25, 34, 40, 44] | 2 | [1, 2, 8, 38, 42, 49] | 1 | [1, 3, 15, 27, 41, 44] | 0 |
