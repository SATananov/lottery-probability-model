# Step 144 — Възпроизводим baseline експеримент

- Experiment ID: `EXP-144-0e11bccbcb-98bfe5488b`
- Dataset SHA-256: `0e11bccbcb47ae6d34f32c5e791ca76cf199aca2ebefe77798c16ab4b4fbc579`
- Dataset latest draw: **2026-53**
- Initial training draws: **9823**
- Holdout draws: **240**
- Package size: **12** combinations
- Random trials: **50**
- Seed: **1442026**

## Основни резултати

- Frequency baseline average best hits: **1.558333**
- Uniform-random mean average best hits: **2.072250**
- Difference: **-0.513917**
- Frequency percentile among random trials: **0.0%**

## Възпроизводимост

- Configuration hash: `98bfe5488b5bdeb2f939eb5d461dad1fa4f782dad590487a28c9c19ed67990fb`
- Code hash: `f8087d2542e894c89ea1ec131e41f1a04e412f6e60ff08ddbb548655a8d6b1a2`
- Result signature: `6dfdb5c332d01bcfc0d5aaf7199f55e60d8909db0a1608f45bcc23bc9d997184`
- Command: `python tools/run_reproducible_baseline_experiment.py --holdout-draws 240 --minimum-training-draws 500 --package-size 12 --random-trials 50 --frequency-pool-size 18 --seed 1442026`

## Ограничения

Лабораторията прави детерминиран walk-forward исторически тест с ясно отделен holdout период. Това е сравнение на baselines, а не доказателство за предвидимост и не е гаранция за печалба.

The frequency baseline does not exceed the random-trial mean on this historical holdout.
