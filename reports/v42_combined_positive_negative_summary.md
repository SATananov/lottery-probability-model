# V42 Combined Positive/Negative Analysis Foundation

This report introduces a reverse analysis layer for the lottery project.
It compares positive historical signals with negative absence-risk signals.

**Important:** This is not a winning guarantee. Lottery draws are random.
The output is a statistical learning artifact, not a promise of future results.

## Dataset

- Valid draw events analyzed: 10059
- Invalid/skipped rows: 0
- Expected hits per number: 1231.714

## Combined 6-number statistical suggestion

- Numbers: 11, 13, 37, 38, 42, 48
- Average positive signal: 87.911
- Average absence risk: 7.595
- Average combined score: 60.825

## Top combined-score numbers

| Number | Positive score | Absence risk | Combined score | Current absence gap | Total hits |
|---:|---:|---:|---:|---:|---:|
| 37 | 96.358 | 7.393 | 65.495 | 4 | 1276 |
| 48 | 87.718 | 6.107 | 60.821 | 0 | 1270 |
| 42 | 85.524 | 6.696 | 60.341 | 1 | 1236 |
| 38 | 87.072 | 10.26 | 60.062 | 9 | 1231 |
| 11 | 85.32 | 5.786 | 59.327 | 0 | 1274 |
| 13 | 85.472 | 9.327 | 58.905 | 1 | 1215 |
| 49 | 85.635 | 7.5 | 58.87 | 6 | 1274 |
| 2 | 86.552 | 12.205 | 58.709 | 8 | 1222 |
| 1 | 82.686 | 7.446 | 57.809 | 3 | 1251 |
| 16 | 86.119 | 12.19 | 57.797 | 1 | 1202 |
| 44 | 84.316 | 8.25 | 57.183 | 0 | 1292 |
| 22 | 81.604 | 8.464 | 56.784 | 2 | 1250 |

## Numbers with high historical absence-risk signal

| Number | Absence risk | Risk level | Current absence gap | Max absence gap | Total hits |
|---:|---:|---|---:|---:|---:|
| 41 | 33.645 | low | 19 | 79 | 1173 |
| 34 | 32.967 | low | 30 | 77 | 1291 |
| 25 | 30.556 | low | 25 | 72 | 1240 |
| 31 | 30.043 | low | 12 | 50 | 1179 |
| 32 | 26.647 | low | 11 | 66 | 1204 |
| 27 | 26.47 | low | 13 | 79 | 1199 |
| 40 | 25.973 | low | 2 | 85 | 1166 |
| 23 | 24.255 | very_low | 13 | 70 | 1169 |
| 21 | 22.629 | very_low | 20 | 46 | 1289 |
| 10 | 20.895 | very_low | 4 | 62 | 1201 |
| 3 | 20.453 | very_low | 10 | 68 | 1182 |
| 18 | 20.051 | very_low | 16 | 68 | 1196 |

## Interpretation

- Positive score looks for stronger historical activity and support from existing v41 outputs.
- Absence-risk score looks for underrepresentation, long current gaps, and weak recent activity.
- Combined score balances both sides and selects 6 numbers with simple diversification rules.
- This analysis can help explain risk, but it cannot know future random lottery events.
