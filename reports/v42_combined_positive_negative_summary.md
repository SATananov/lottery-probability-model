# V42 Combined Positive/Negative Analysis Foundation

This report introduces a reverse analysis layer for the lottery project.
It compares positive historical signals with negative absence-risk signals.

**Important:** This is not a winning guarantee. Lottery draws are random.
The output is a statistical learning artifact, not a promise of future results.

## Dataset

- Valid draw events analyzed: 10060
- Invalid/skipped rows: 0
- Expected hits per number: 1231.837

## Combined 6-number statistical suggestion

- Numbers: 2, 4, 17, 37, 38, 42
- Average positive signal: 89.488
- Average absence risk: 6.944
- Average combined score: 62.094

## Top combined-score numbers

| Number | Positive score | Absence risk | Combined score | Current absence gap | Total hits |
|---:|---:|---:|---:|---:|---:|
| 38 | 96.09 | 6.75 | 67.006 | 0 | 1232 |
| 2 | 95.796 | 8.638 | 65.824 | 0 | 1223 |
| 37 | 96.189 | 7.768 | 65.251 | 5 | 1276 |
| 42 | 82.855 | 7.071 | 58.548 | 2 | 1236 |
| 33 | 83.542 | 8.548 | 58.423 | 0 | 1228 |
| 4 | 84.222 | 6.4 | 58.319 | 0 | 1277 |
| 17 | 81.775 | 5.036 | 57.613 | 0 | 1268 |
| 11 | 82.651 | 6.161 | 57.533 | 1 | 1274 |
| 36 | 83.128 | 12.178 | 56.56 | 11 | 1221 |
| 48 | 80.048 | 6.482 | 55.928 | 1 | 1270 |
| 22 | 78.934 | 9.239 | 54.839 | 3 | 1250 |
| 28 | 77.361 | 6.696 | 54.797 | 3 | 1251 |

## Numbers with high historical absence-risk signal

| Number | Absence risk | Risk level | Current absence gap | Max absence gap | Total hits |
|---:|---:|---|---:|---:|---:|
| 41 | 34.042 | low | 20 | 79 | 1173 |
| 34 | 33.342 | low | 31 | 77 | 1291 |
| 25 | 30.931 | low | 26 | 72 | 1240 |
| 31 | 30.44 | low | 13 | 50 | 1179 |
| 32 | 30.311 | low | 12 | 66 | 1204 |
| 27 | 26.868 | low | 14 | 79 | 1199 |
| 40 | 26.37 | low | 3 | 85 | 1166 |
| 23 | 24.652 | very_low | 14 | 70 | 1169 |
| 21 | 23.004 | very_low | 21 | 46 | 1289 |
| 10 | 21.292 | very_low | 5 | 62 | 1201 |
| 3 | 20.851 | very_low | 11 | 68 | 1182 |
| 18 | 20.449 | very_low | 17 | 68 | 1196 |

## Interpretation

- Positive score looks for stronger historical activity and support from existing v41 outputs.
- Absence-risk score looks for underrepresentation, long current gaps, and weak recent activity.
- Combined score balances both sides and selects 6 numbers with simple diversification rules.
- This analysis can help explain risk, but it cannot know future random lottery events.
