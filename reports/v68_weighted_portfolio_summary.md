# Step 68 — Weighted Portfolio Optimizer

This report evaluates the Step 67 ticket set as one statistical portfolio.

**Important:** This is a portfolio analysis tool. It is not a prediction and not a гаранция за печалба.

Tickets analyzed: **8**
Unique numbers covered: **18 / 49**
Coverage: **36.73%**
Covered top 10 Step 66 numbers: **10 / 10**
Covered top 20 Step 66 numbers: **17 / 20**
Average ticket Step 66 score: **75.139%**
Average ticket overlap: **1.893**
Max ticket overlap: **3**
Repeated pairs: **25**
Repeated triples: **4**
Portfolio score: **59.658 / 100**
Portfolio status: **приемлив портфейл с нужда от наблюдение**

## Recommendations

- Портфолиото покрива сравнително малко уникални числа. Следваща оптимизация може да увеличи diversity.
- Има силни Step 66 числа, които не са покрити в портфолиото: 11, 24, 12.
- Има повторени двойки. Това не е грешка, но оптимизаторът на пакет от комбинации може да намали повторенията.
- Има повторени тройки. Това повишава концентрацията и може да се оптимизира.

## Ticket contribution analysis

| Ticket | Strategy | Numbers | Avg Step 66 score | Unique help | Top20 count | Max overlap | Portfolio contribution |
|---:|---|---|---:|---:|---:|---:|---:|
| 5 | Балансирана комбинация по ниски/високи числа | 1,3,22,38,42,49 | 72.61% | 2 | 6 | 2 | 59.935 |
| 1 | Балансирана претеглена комбинация | 1,2,4,18,37,49 | 83.167% | 0 | 6 | 3 | 51.742 |
| 6 | Разпределена диапазонна комбинация | 1,13,22,34,37,48 | 73.785% | 1 | 6 | 3 | 51.582 |
| 7 | Консервативно ядро | 2,4,17,22,29,38 | 69.893% | 1 | 5 | 2 | 50.441 |
| 3 | Диверсифицирана претеглена комбинация | 2,13,21,23,38,49 | 71.622% | 0 | 6 | 2 | 49.392 |
| 8 | Разширена статистическа комбинация | 1,18,21,23,34,37 | 78.371% | 0 | 6 | 3 | 49.104 |
| 2 | Комбинация с висока претеглена оценка | 1,4,21,34,38,44 | 77.633% | 0 | 6 | 3 | 48.698 |
| 4 | Балансирана комбинация по нечетни/четни числа | 2,17,23,34,37,44 | 74.028% | 0 | 6 | 3 | 46.716 |

## Under-covered top Step 66 numbers

- Number 11 — Step 66 rank 13, score 64.449%
- Number 24 — Step 66 rank 17, score 57.553%
- Number 12 — Step 66 rank 20, score 55.437%

## Safety note

Lottery draws are random. This step only evaluates structure, coverage and overlap inside a статистическа референция portfolio.
