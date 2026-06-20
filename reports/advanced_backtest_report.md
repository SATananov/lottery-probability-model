# Advanced Backtesting Report

Rolling backtest: each step trains on past draws only and tests against the next real draw.

- Tested draws: 40
- Minimum training size: 300
- Candidate limit per step: 800
- Best strategy: frequency_stability

Best average-match strategy in this backtest: frequency_stability. Treat this as a model check, not proof that future lottery draws are predictable.

## Average matches

| Strategy | Average matches | >=3 hit rate | >=4 hit rate |
|:---|---:|---:|---:|
| advanced | 0.6250 | 0.00% | 0.00% |
| time_decay | 0.7250 | 2.50% | 0.00% |
| bayesian | 0.6250 | 0.00% | 0.00% |
| gap | 0.8750 | 10.00% | 0.00% |
| frequency_stability | 0.9500 | 2.50% | 2.50% |
| random | 0.8250 | 2.50% | 0.00% |

## Match distributions

| Strategy | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|:---|---:|---:|---:|---:|---:|---:|---:|
| advanced | 18 | 19 | 3 | 0 | 0 | 0 | 0 |
| time_decay | 18 | 16 | 5 | 1 | 0 | 0 | 0 |
| bayesian | 20 | 15 | 5 | 0 | 0 | 0 | 0 |
| gap | 16 | 17 | 3 | 4 | 0 | 0 | 0 |
| frequency_stability | 9 | 26 | 4 | 0 | 1 | 0 | 0 |
| random | 15 | 18 | 6 | 1 | 0 | 0 | 0 |

## Recent tested draws

- Draw 9981 (): actual=[11, 25, 31, 38, 40, 45], advanced=[6, 11, 21, 34, 44, 49] (1 matches), random=[8, 26, 28, 32, 36, 38] (1 matches)
- Draw 9982 (): actual=[5, 10, 14, 33, 34, 38], advanced=[6, 21, 22, 34, 37, 49] (1 matches), random=[17, 26, 32, 33, 34, 39] (2 matches)
- Draw 9983 (): actual=[17, 24, 25, 28, 37, 49], advanced=[6, 21, 22, 34, 37, 49] (2 matches), random=[2, 27, 31, 33, 34, 37] (1 matches)
- Draw 9984 (): actual=[2, 8, 16, 23, 39, 43], advanced=[6, 21, 22, 29, 39, 46] (1 matches), random=[4, 9, 15, 34, 37, 43] (1 matches)
- Draw 9985 (): actual=[3, 20, 24, 28, 31, 46], advanced=[6, 21, 22, 29, 34, 46] (1 matches), random=[7, 10, 28, 31, 40, 46] (3 matches)
- Draw 9986 (): actual=[3, 4, 16, 25, 28, 36], advanced=[1, 21, 22, 29, 34, 42] (0 matches), random=[8, 15, 30, 31, 41, 45] (0 matches)
- Draw 9987 (): actual=[4, 12, 30, 42, 48, 49], advanced=[9, 21, 22, 29, 34, 42] (1 matches), random=[17, 31, 35, 36, 44, 46] (0 matches)
- Draw 9988 (): actual=[13, 17, 23, 33, 34, 38], advanced=[6, 21, 22, 29, 34, 37] (1 matches), random=[20, 26, 33, 36, 42, 43] (1 matches)
- Draw 9989 (): actual=[13, 17, 28, 32, 46, 47], advanced=[6, 21, 22, 29, 34, 37] (0 matches), random=[13, 19, 26, 28, 31, 45] (2 matches)
- Draw 9990 (): actual=[5, 11, 21, 28, 39, 43], advanced=[6, 21, 22, 29, 34, 37] (1 matches), random=[1, 3, 10, 18, 39, 42] (1 matches)
- Draw 9991 (): actual=[27, 33, 38, 45, 46, 49], advanced=[6, 9, 22, 29, 35, 44] (0 matches), random=[13, 17, 24, 30, 32, 34] (0 matches)
- Draw 9992 (): actual=[7, 17, 18, 25, 30, 42], advanced=[6, 9, 22, 29, 37, 44] (0 matches), random=[28, 30, 32, 33, 45, 48] (1 matches)
- Draw 9993 (): actual=[12, 16, 26, 34, 37, 40], advanced=[6, 9, 22, 29, 37, 44] (1 matches), random=[3, 19, 21, 30, 36, 43] (0 matches)
- Draw 9994 (): actual=[4, 6, 10, 18, 23, 25], advanced=[6, 9, 22, 29, 35, 44] (1 matches), random=[7, 17, 29, 33, 45, 46] (0 matches)
- Draw 9995 (): actual=[3, 14, 20, 27, 33, 35], advanced=[9, 15, 22, 29, 34, 44] (0 matches), random=[5, 12, 28, 29, 31, 42] (0 matches)
- Draw 9996 (): actual=[3, 9, 27, 31, 35, 36], advanced=[9, 15, 22, 29, 34, 44] (1 matches), random=[7, 13, 18, 24, 27, 32] (1 matches)
- Draw 9997 (): actual=[14, 21, 32, 38, 40, 49], advanced=[1, 21, 22, 29, 34, 44] (1 matches), random=[1, 6, 10, 29, 47, 48] (0 matches)
- Draw 9998 (): actual=[1, 12, 24, 27, 31, 43], advanced=[1, 15, 22, 29, 34, 44] (1 matches), random=[6, 13, 16, 35, 38, 40] (0 matches)
- Draw 9999 (): actual=[3, 15, 26, 33, 47, 48], advanced=[11, 15, 22, 29, 34, 44] (1 matches), random=[3, 8, 18, 35, 40, 43] (1 matches)
- Draw 10000 (): actual=[2, 14, 21, 27, 28, 48], advanced=[8, 11, 22, 29, 34, 44] (0 matches), random=[1, 10, 21, 23, 41, 49] (1 matches)
- Draw 10001 (): actual=[10, 16, 24, 27, 30, 36], advanced=[8, 11, 22, 29, 34, 44] (0 matches), random=[9, 32, 37, 38, 43, 45] (0 matches)
- Draw 10002 (): actual=[2, 6, 7, 19, 29, 41], advanced=[8, 11, 22, 29, 34, 44] (1 matches), random=[9, 15, 31, 35, 38, 39] (0 matches)
- Draw 10003 (): actual=[2, 24, 31, 36, 40, 48], advanced=[8, 11, 22, 34, 37, 44] (0 matches), random=[6, 19, 27, 33, 43, 45] (0 matches)
- Draw 10004 (): actual=[3, 9, 10, 13, 20, 30], advanced=[8, 11, 22, 34, 37, 42] (0 matches), random=[9, 11, 20, 27, 33, 38] (2 matches)
- Draw 10005 (): actual=[2, 6, 7, 8, 29, 39], advanced=[8, 11, 22, 34, 37, 42] (1 matches), random=[1, 10, 13, 25, 34, 49] (0 matches)
- Draw 10006 (): actual=[11, 15, 25, 38, 40, 44], advanced=[11, 21, 22, 34, 37, 42] (1 matches), random=[4, 5, 7, 23, 25, 42] (1 matches)
- Draw 10007 (): actual=[7, 16, 24, 29, 31, 46], advanced=[17, 21, 22, 34, 37, 42] (0 matches), random=[2, 21, 23, 31, 33, 48] (1 matches)
- Draw 10008 (): actual=[2, 3, 15, 18, 21, 25], advanced=[17, 21, 22, 34, 37, 42] (1 matches), random=[8, 20, 21, 29, 32, 44] (1 matches)
- Draw 10009 (): actual=[20, 22, 24, 32, 35, 49], advanced=[9, 17, 22, 34, 37, 42] (1 matches), random=[10, 11, 30, 37, 38, 40] (0 matches)
- Draw 10010 (): actual=[5, 21, 26, 28, 46, 48], advanced=[4, 17, 23, 34, 37, 42] (0 matches), random=[14, 22, 28, 30, 34, 40] (1 matches)
