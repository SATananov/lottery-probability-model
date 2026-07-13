# V42 Combined Positive/Negative Analysis Foundation

This report introduces a reverse analysis layer for the lottery project.
It compares positive historical signals with negative absence-risk signals.

**Important:** This is not a winning guarantee. Lottery draws are random.
The output is a statistical learning artifact, not a promise of future results.

## Dataset

- Valid draw events analyzed: 10064
- Invalid/skipped rows: 0
- Expected hits per number: 1232.327

## Combined 6-number statistical suggestion

- Numbers: 2, 11, 37, 38, 48, 49
- Average positive signal: 86.33
- Average absence risk: 7.294
- Average combined score: 59.786

## Top combined-score numbers

| Number | Positive score | Absence risk | Combined score | Current absence gap | Total hits |
|---:|---:|---:|---:|---:|---:|
| 37 | 97.033 | 5.893 | 66.471 | 0 | 1277 |
| 38 | 88.456 | 7.125 | 62.081 | 1 | 1234 |
| 49 | 82.951 | 6.0 | 57.764 | 2 | 1275 |
| 2 | 83.477 | 10.23 | 57.565 | 4 | 1223 |
| 11 | 82.943 | 6.536 | 57.556 | 2 | 1275 |
| 48 | 83.121 | 7.982 | 57.279 | 5 | 1270 |
| 16 | 82.936 | 11.339 | 56.16 | 0 | 1203 |
| 44 | 82.272 | 8.25 | 55.904 | 0 | 1293 |
| 36 | 79.639 | 8.705 | 55.733 | 2 | 1222 |
| 30 | 78.775 | 7.661 | 55.453 | 1 | 1247 |
| 17 | 78.318 | 5.411 | 55.311 | 1 | 1269 |
| 4 | 79.348 | 6.75 | 55.148 | 2 | 1278 |

## Numbers with high historical absence-risk signal

| Number | Absence risk | Risk level | Current absence gap | Max absence gap | Total hits |
|---:|---:|---|---:|---:|---:|
| 32 | 35.168 | low | 16 | 66 | 1204 |
| 34 | 34.842 | low | 35 | 77 | 1291 |
| 25 | 32.431 | low | 30 | 72 | 1240 |
| 31 | 32.029 | low | 17 | 50 | 1179 |
| 27 | 31.724 | low | 18 | 79 | 1199 |
| 10 | 29.416 | low | 9 | 62 | 1201 |
| 40 | 27.957 | low | 7 | 85 | 1166 |
| 41 | 23.55 | very_low | 1 | 79 | 1174 |
| 3 | 22.84 | very_low | 15 | 68 | 1182 |
| 43 | 21.96 | very_low | 10 | 87 | 1222 |
| 14 | 20.622 | very_low | 8 | 55 | 1207 |
| 23 | 19.676 | very_low | 1 | 70 | 1170 |

## Interpretation

- Positive score looks for stronger historical activity and support from existing v41 outputs.
- Absence-risk score looks for underrepresentation, long current gaps, and weak recent activity.
- Combined score balances both sides and selects 6 numbers with simple diversification rules.
- This analysis can help explain risk, but it cannot know future random lottery events.
