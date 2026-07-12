# Step 146 — Controlled Neural Experiment Expansion & Robustness Validation

- Experiment ID: `EXP-146-0e11bccbcb-0e4ec3757b`
- Dataset SHA-256: `0e11bccbcb47ae6d34f32c5e791ca76cf199aca2ebefe77798c16ab4b4fbc579`
- Latest draw: **2026-53**
- Historical folds: **3 × 120 draws**
- Random seeds: **5**
- Robustness runs: **15**
- Promotion gate: **BLOCKED**

## Aggregate average best hits

| Strategy | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| neural_dynamics_reservoir | 2.012222 | 0.052517 | 1.950000 | 2.150000 |
| frequency_walk_forward | 2.008333 | 0.053403 | 1.891667 | 2.091667 |
| recency_weighted_walk_forward | 2.035000 | 0.043695 | 1.966667 | 2.125000 |
| recent_window_frequency | 2.017222 | 0.051141 | 1.925000 | 2.108333 |
| frequency_recency_blend | 2.035556 | 0.047480 | 1.958333 | 2.116667 |
| uniform_random_mean | 2.073611 | 0.020980 | 2.018333 | 2.107500 |

## Confidence and stability comparison

| Baseline | Mean advantage | 95% CI | Sign p | Positive seeds | Positive folds |
|---|---:|---:|---:|---:|---:|
| frequency_walk_forward | 0.003889 | [-0.041667, 0.052222] | 1.000000 | 40.0% | 33.3% |
| recency_weighted_walk_forward | -0.022778 | [-0.057778, 0.010000] | 0.790527 | 20.0% | 33.3% |
| recent_window_frequency | -0.005000 | [-0.035000, 0.025556] | 0.607239 | 40.0% | 33.3% |
| frequency_recency_blend | -0.023333 | [-0.061111, 0.018889] | 0.301758 | 40.0% | 33.3% |
| uniform_random_mean | -0.061389 | [-0.085944, -0.033056] | 0.000977 | 0.0% | 0.0% |

## Promotion requirements

- all_mean_advantages_positive: **FAIL**
- all_confidence_intervals_above_zero: **FAIL**
- all_sign_tests_significant: **FAIL**
- all_seed_positive_rates_sufficient: **FAIL**
- all_fold_positive_rates_sufficient: **FAIL**
- neural_seed_spread_within_limit: **PASS**
- minimum_design_size_met: **PASS**

## Conclusion

The neural robustness experiment did not pass every multi-seed, multi-period confidence and stability gate. The model remains research-only and isolated from ticket generation.

Step 146 е изолиран robustness експеримент върху исторически тиражи. Той не е свързан с production pipeline, не създава реални фишове и не доказва предвидимост на бъдещи случайни тиражи.
