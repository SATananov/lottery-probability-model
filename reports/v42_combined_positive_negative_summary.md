# V42 Combined Positive/Negative Analysis Foundation

This report introduces a reverse analysis layer for the lottery project.
It compares positive historical signals with negative absence-risk signals.

**Important:** This is not a winning guarantee. Lottery draws are random.
The output is a statistical learning artifact, not a promise of future results.

## Dataset

- Valid draw events analyzed: 10058
- Invalid/skipped rows: 0
- Expected hits per number: 1231.592

## Combined 6-number statistical suggestion

- Numbers: 2, 13, 37, 38, 42, 49
- Average positive signal: 88.003
- Average absence risk: 8.51
- Average combined score: 60.69

## Top combined-score numbers

| Number | Positive score | Absence risk | Combined score | Current absence gap | Total hits |
|---:|---:|---:|---:|---:|---:|
| 37 | 96.528 | 7.018 | 65.738 | 3 | 1276 |
| 42 | 86.086 | 6.321 | 60.828 | 0 | 1236 |
| 38 | 87.241 | 9.862 | 60.323 | 8 | 1231 |
| 13 | 85.641 | 8.929 | 59.165 | 0 | 1215 |
| 49 | 85.804 | 7.125 | 59.114 | 5 | 1274 |
| 2 | 86.721 | 11.807 | 58.969 | 7 | 1222 |
| 16 | 86.288 | 11.792 | 58.057 | 0 | 1202 |
| 1 | 82.855 | 7.071 | 58.053 | 2 | 1251 |
| 22 | 83.08 | 8.089 | 57.838 | 1 | 1250 |
| 11 | 83.103 | 6.911 | 57.553 | 3 | 1273 |
| 44 | 82.599 | 8.65 | 55.995 | 0 | 1291 |
| 28 | 78.091 | 5.946 | 55.527 | 1 | 1251 |

## Numbers with high historical absence-risk signal

| Number | Absence risk | Risk level | Current absence gap | Max absence gap | Total hits |
|---:|---:|---|---:|---:|---:|
| 41 | 33.248 | low | 18 | 79 | 1173 |
| 34 | 32.592 | low | 29 | 77 | 1291 |
| 25 | 30.181 | low | 24 | 72 | 1240 |
| 31 | 29.646 | low | 11 | 50 | 1179 |
| 47 | 27.033 | low | 18 | 63 | 1214 |
| 32 | 26.249 | low | 10 | 66 | 1204 |
| 27 | 26.072 | low | 12 | 79 | 1199 |
| 40 | 25.576 | low | 1 | 85 | 1166 |
| 23 | 23.858 | very_low | 12 | 70 | 1169 |
| 10 | 20.497 | very_low | 3 | 62 | 1201 |
| 3 | 20.056 | very_low | 9 | 68 | 1182 |
| 18 | 19.654 | very_low | 15 | 68 | 1196 |

## Interpretation

- Positive score looks for stronger historical activity and support from existing v41 outputs.
- Absence-risk score looks for underrepresentation, long current gaps, and weak recent activity.
- Combined score balances both sides and selects 6 numbers with simple diversification rules.
- This analysis can help explain risk, but it cannot know future random lottery events.
