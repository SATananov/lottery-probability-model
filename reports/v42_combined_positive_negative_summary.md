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

- Numbers: 22, 28, 37, 38, 42, 49
- Average positive signal: 87.805
- Average absence risk: 7.393
- Average combined score: 60.928

## Top combined-score numbers

| Number | Positive score | Absence risk | Combined score | Current absence gap | Total hits |
|---:|---:|---:|---:|---:|---:|
| 37 | 96.528 | 7.018 | 65.738 | 3 | 1276 |
| 38 | 89.741 | 9.862 | 61.873 | 8 | 1231 |
| 49 | 88.304 | 7.125 | 60.664 | 5 | 1274 |
| 22 | 85.58 | 8.089 | 59.388 | 1 | 1250 |
| 42 | 83.586 | 6.321 | 59.278 | 0 | 1236 |
| 28 | 83.091 | 5.946 | 58.627 | 1 | 1251 |
| 2 | 84.221 | 11.807 | 57.419 | 7 | 1222 |
| 24 | 83.377 | 11.036 | 57.227 | 12 | 1240 |
| 36 | 83.467 | 11.382 | 57.08 | 9 | 1221 |
| 26 | 81.491 | 8.761 | 56.786 | 1 | 1219 |
| 13 | 78.141 | 8.929 | 54.515 | 0 | 1215 |
| 30 | 77.877 | 8.786 | 54.478 | 4 | 1246 |

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
