# Middle Model Отчет от историческа проверка

## Goal

This report checks whether the middle/balanced model performs better than hot, cold, and random baselines on later draws.

## Summary

- Проверени тиражи: 10047
- Минимален обучаващ период: 10
- Последен прозорец: 20
- Случайно семе: 123
- Middle average matches: 0.7469
- Hot average matches: 0.7343
- Cold average matches: 0.7163
- Random average matches: 0.7322

## Conclusion

Best average in this run: middle model. Middle=0.7469, Hot=0.7343, Cold=0.7163, Random=0.7322. The sample is larger, but the result still needs cautious interpretation.

## Match distribution

| Matches | Middle count | Hot count | Cold count | Random count |
|---:|---:|---:|---:|---:|
| 0 | 4326 | 4369 | 4497 | 4426 |
| 1 | 4147 | 4161 | 4079 | 4098 |
| 2 | 1377 | 1340 | 1306 | 1318 |
| 3 | 185 | 171 | 154 | 198 |
| 4 | 12 | 6 | 11 | 7 |
| 5 | 0 | 0 | 0 | 0 |
| 6 | 0 | 0 | 0 | 0 |

## Tested draw detail

The complete row-level table is intentionally not stored in Markdown. It is reproducible by rerunning the corresponding backtest script; only a small head/tail sample is retained here for review.

| Draw ID | Date | Actual numbers | Middle ticket | Middle matches | Hot ticket | Hot matches | Cold ticket | Cold matches | Random ticket | Random matches |
|:---|:---|:---|:---|---:|:---|---:|:---|---:|:---|---:|
| 11 |  | [7, 8, 11, 19, 29, 30] | [2, 6, 12, 13, 25, 46] | 0 | [8, 10, 18, 22, 38, 49] | 1 | [3, 4, 5, 11, 16, 17] | 1 | [4, 6, 7, 18, 27, 48] | 1 |
| 12 |  | [2, 16, 18, 27, 34, 47] | [2, 6, 13, 14, 24, 46] | 1 | [8, 10, 18, 22, 38, 49] | 1 | [3, 4, 5, 16, 17, 20] | 1 | [3, 22, 25, 35, 36, 45] | 0 |
| 13 |  | [9, 11, 21, 30, 33, 48] | [14, 24, 26, 31, 33, 42] | 1 | [8, 10, 18, 22, 38, 49] | 0 | [3, 4, 5, 17, 20, 35] | 0 | [4, 9, 11, 22, 36, 46] | 2 |
| … | … | … | … | … |
| 10055 | 2026-06-11 | [1, 10, 11, 15, 16, 37] | [5, 20, 24, 27, 31, 36] | 0 | [2, 8, 13, 38, 42, 49] | 0 | [10, 12, 22, 25, 34, 44] | 1 | [8, 24, 26, 33, 44, 46] | 0 |
| 10056 | 2026-06-14 | [1, 7, 8, 14, 29, 42] | [3, 5, 7, 27, 32, 36] | 1 | [1, 2, 8, 38, 42, 49] | 3 | [12, 22, 25, 34, 40, 44] | 0 | [11, 20, 24, 26, 29, 36] | 1 |
| 10057 | 2026-06-18 | [22, 26, 28, 29, 40, 42] | [3, 5, 33, 36, 45, 46] | 0 | [1, 2, 8, 38, 42, 49] | 1 | [12, 22, 25, 34, 40, 44] | 2 | [5, 14, 16, 19, 34, 37] | 0 |
