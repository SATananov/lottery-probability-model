# Step 66 — Претеглена обединена оценка

This report combines available number-score sources with Step 65 adaptive model weights.

**Important:** This is statistical signal management only. It is not a guarantee and not a promise of future lottery results.

Sources used: **8**
Numbers scored: **49**
Top weighted number: **1**
Top претеглена оценка: **100.0%**

## Sources used

| Model | Original Step 65 weight | Used Step 66 weight | Files |
|---|---:|---:|---|
| v44.1 — финална обединена комбинация | 0.201660 | 0.230903 | reports/v44_1_final_ensemble_number_scores.csv<br>reports/v44_1_final_ensemble_ticket_summary.json<br>models/v44_1/v44_1_final_ensemble_number_scores.json<br>models/v44_1/v44_1_final_ensemble_ticket_prediction.json |
| v42 — комбиниран позитивен/негативен модел | 0.180926 | 0.207163 | models/v42/v42_combined_prediction.json<br>reports/v42_combined_positive_negative_scores.csv<br>reports/v42_combined_positive_negative_summary.json<br>models/v42/v42_positive_negative_number_scores.json |
| v41 — последни прогнозни сигнали | 0.162459 | 0.186018 | models/v41/v41_latest_predictions.json<br>models/v41/v41_frequency_main_numbers_model.json<br>models/v41/v41_recency_main_numbers_model.json<br>reports/v41_bst_official_archive_audit.json<br>reports/v41_canonical_draw_events_audit.json<br>reports/v41_model_retraining_summary.json<br>reports/v41_training_readiness_audit.json<br>models/v41/v41_sgd_number_model_metadata.json |
| v45 — Prediction Dashboard Pro | 0.075012 | 0.085890 | models/v45/v45_final_prediction_tickets.json<br>reports/v45_training_summary.json<br>models/v45/v45_latest_number_scores.json<br>models/v45/v45_model_metadata.json |
| v51 — пакет от комбинации | 0.063324 | 0.072507 | reports/v51_current_pro_ticket_score.csv |
| v57 — горещи, студени и стабилни | 0.063324 | 0.072507 | reports/v57_hot_cold_stable_numbers.csv<br>reports/v57_hot_cold_stable_numbers.json<br>reports/v57_hot_cold_stable_summary.json |
| v58 — обединена оценка | 0.063324 | 0.072507 | reports/v58_smart_ensemble_scores_sample.csv<br>reports/v58_smart_ensemble_scores_sample.json |
| v59 — интелигентен генератор 2 | 0.063324 | 0.072507 | reports/v59_smart_ticket_builder_2_summary.json<br>reports/v59_smart_ticket_builder_2_sample.csv<br>reports/v59_smart_ticket_builder_2_sample.json |

## Top weighted numbers

| Rank | Number | Претеглена оценка % | Source count | Status |
|---:|---:|---:|---:|---|
| 1 | 1 | 100.0% | 7 | водещ претеглен сигнал |
| 2 | 2 | 90.106% | 8 | водещ претеглен сигнал |
| 3 | 37 | 83.931% | 6 | водещ претеглен сигнал |
| 4 | 4 | 79.622% | 8 | водещ претеглен сигнал |
| 5 | 18 | 74.232% | 7 | силен потвърден сигнал |
| 6 | 34 | 73.785% | 8 | силен потвърден сигнал |
| 7 | 38 | 73.752% | 6 | силен потвърден сигнал |
| 8 | 22 | 72.427% | 6 | силен потвърден сигнал |
| 9 | 21 | 71.601% | 8 | силен потвърден сигнал |
| 10 | 49 | 71.111% | 6 | силен потвърден сигнал |
| 11 | 44 | 67.041% | 7 | силен потвърден сигнал |
| 12 | 23 | 66.675% | 5 | силен потвърден сигнал |
| 13 | 11 | 64.449% | 5 | силен потвърден сигнал |
| 14 | 17 | 62.632% | 8 | силен потвърден сигнал |
| 15 | 42 | 59.857% | 7 | балансиран сигнал |

## Reference combinations

These are референтни комбинации built from weighted statistical signals. They are not гаранция за печалбаs.

- Ticket 1: 1, 2, 4, 18, 34, 37
- Ticket 2: 2, 17, 18, 22, 24, 44
- Ticket 3: 13, 21, 23, 34, 37, 42
- Ticket 4: 3, 4, 11, 38, 48, 49

## Skipped sources

- v50_pair_group_intelligence: no parseable score source files found
- v61_latest_draw_signal_hits: post-draw analyzer; used for reliability context, not direct score source
