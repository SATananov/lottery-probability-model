# V42 Combined Positive/Negative Analysis Foundation

This report introduces a reverse analysis layer for the lottery project.
It compares positive historical signals with negative absence-risk signals.

**Important:** This is not a winning guarantee. Lottery draws are random.
The output is a statistical learning artifact, not a promise of future results.

## Dataset

- Valid draw events analyzed: 10057
- Invalid/skipped rows: 0
- Expected hits per number: 1231.469

## Combined 6-number statistical suggestion

- Numbers: 22, 28, 37, 38, 42, 49
- Average positive signal: 87.66
- Average absence risk: 7.077
- Average combined score: 60.961

## Top combined-score numbers

| Number | Positive score | Absence risk | Combined score | Current absence gap | Total hits |
|---:|---:|---:|---:|---:|---:|
| 37 | 96.697 | 6.643 | 65.981 | 2 | 1276 |
| 38 | 89.91 | 9.464 | 62.133 | 7 | 1231 |
| 49 | 88.473 | 6.75 | 60.907 | 4 | 1274 |
| 22 | 85.749 | 7.714 | 59.631 | 0 | 1250 |
| 28 | 83.261 | 5.571 | 58.87 | 0 | 1251 |
| 42 | 81.868 | 6.321 | 58.242 | 0 | 1235 |
| 2 | 84.39 | 11.409 | 57.679 | 6 | 1222 |
| 24 | 83.546 | 10.661 | 57.471 | 11 | 1240 |
| 36 | 83.636 | 10.984 | 57.34 | 8 | 1221 |
| 26 | 81.66 | 8.363 | 57.046 | 0 | 1219 |
| 30 | 78.047 | 8.411 | 54.721 | 3 | 1246 |
| 48 | 80.895 | 12.857 | 54.05 | 18 | 1269 |

## Numbers with high historical absence-risk signal

| Number | Absence risk | Risk level | Current absence gap | Max absence gap | Total hits |
|---:|---:|---|---:|---:|---:|
| 41 | 32.851 | low | 17 | 79 | 1173 |
| 34 | 32.217 | low | 28 | 77 | 1291 |
| 25 | 29.806 | low | 23 | 72 | 1240 |
| 31 | 29.249 | low | 10 | 50 | 1179 |
| 47 | 26.635 | low | 17 | 63 | 1214 |
| 27 | 25.675 | low | 11 | 79 | 1199 |
| 40 | 25.179 | low | 0 | 85 | 1166 |
| 23 | 23.461 | very_low | 11 | 70 | 1169 |
| 32 | 22.585 | very_low | 9 | 66 | 1204 |
| 44 | 22.042 | very_low | 27 | 77 | 1290 |
| 10 | 20.099 | very_low | 2 | 62 | 1201 |
| 3 | 19.659 | very_low | 8 | 68 | 1182 |

## Interpretation

- Positive score looks for stronger historical activity and support from existing v41 outputs.
- Absence-risk score looks for underrepresentation, long current gaps, and weak recent activity.
- Combined score balances both sides and selects 6 numbers with simple diversification rules.
- This analysis can help explain risk, but it cannot know future random lottery events.
