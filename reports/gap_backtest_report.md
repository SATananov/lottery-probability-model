# Gap / Interval Model Отчет от историческа проверка

## Goal

This report checks whether the gap/interval probability model performs better than hot, cold, middle, and random baselines.

## Summary

- Проверени тиражи: 10047
- Минимален обучаващ период: 10
- Случайно семе: 456
- Gap average matches: 0.7192
- Hot average matches: 0.7343
- Cold average matches: 0.7163
- Middle average matches: 0.7469
- Random average matches: 0.7334

## Conclusion

Best average in this run: middle model. Gap=0.7192, Hot=0.7343, Cold=0.7163, Middle=0.7469, Random=0.7334. The sample is larger, but the result still needs cautious interpretation.

## Match distribution

| Matches | Gap count | Hot count | Cold count | Middle count | Random count |
|---:|---:|---:|---:|---:|---:|
| 0 | 4503 | 4369 | 4497 | 4326 | 4369 |
| 1 | 4078 | 4161 | 4079 | 4147 | 4164 |
| 2 | 1261 | 1340 | 1306 | 1377 | 1348 |
| 3 | 195 | 171 | 154 | 185 | 156 |
| 4 | 9 | 6 | 11 | 12 | 10 |
| 5 | 1 | 0 | 0 | 0 | 0 |
| 6 | 0 | 0 | 0 | 0 | 0 |

## Tested draw detail

The complete row-level table is intentionally not stored in Markdown. It is reproducible by rerunning the corresponding backtest script; only a small head/tail sample is retained here for review.

| Draw ID | Date | Actual numbers | Gap ticket | Gap matches | Hot ticket | Hot matches | Cold ticket | Cold matches | Middle ticket | Middle matches | Random ticket | Random matches |
|:---|:---|:---|:---|---:|:---|---:|:---|---:|:---|---:|:---|---:|
| 11 |  | [7, 8, 11, 19, 29, 30] | [8, 18, 38, 41, 42, 49] | 1 | [8, 10, 18, 22, 38, 49] | 1 | [3, 4, 5, 11, 16, 17] | 1 | [2, 6, 12, 13, 25, 46] | 0 | [25, 28, 29, 30, 42, 48] | 2 |
| 12 |  | [2, 16, 18, 27, 34, 47] | [7, 8, 18, 22, 38, 41] | 1 | [8, 10, 18, 22, 38, 49] | 1 | [3, 4, 5, 16, 17, 20] | 1 | [2, 6, 13, 14, 24, 46] | 1 | [3, 8, 21, 34, 40, 47] | 2 |
| 13 |  | [9, 11, 21, 30, 33, 48] | [10, 18, 22, 38, 41, 49] | 0 | [8, 10, 18, 22, 38, 49] | 0 | [3, 4, 5, 17, 20, 35] | 0 | [14, 24, 26, 31, 33, 42] | 1 | [6, 8, 30, 31, 32, 45] | 1 |
| … | … | … | … | … |
| 10055 | 2026-06-11 | [1, 10, 11, 15, 16, 37] | [10, 11, 34, 40, 47, 48] | 2 | [2, 8, 13, 38, 42, 49] | 0 | [10, 12, 22, 25, 34, 44] | 1 | [5, 20, 24, 27, 31, 36] | 0 | [2, 12, 17, 38, 47, 49] | 0 |
| 10056 | 2026-06-14 | [1, 7, 8, 14, 29, 42] | [4, 12, 22, 25, 44, 48] | 0 | [1, 2, 8, 38, 42, 49] | 3 | [12, 22, 25, 34, 40, 44] | 0 | [3, 5, 7, 27, 32, 36] | 1 | [9, 21, 41, 42, 43, 45] | 1 |
| 10057 | 2026-06-18 | [22, 26, 28, 29, 40, 42] | [12, 18, 25, 40, 44, 48] | 1 | [1, 2, 8, 38, 42, 49] | 1 | [12, 22, 25, 34, 40, 44] | 2 | [3, 5, 33, 36, 45, 46] | 0 | [4, 27, 33, 45, 46, 48] | 0 |
