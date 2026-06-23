# Step 66 — Weighted Smart Комбиниран анализ Integration

This report combines available number-score sources with Step 65 adaptive model weights.

**Important:** This is statistical signal management only. It is not a guarantee and not a promise of future lottery results.

Sources used: **8**
Numbers scored: **49**
Top weighted number: **1**
Top претеглена оценка: **100.0%**

## Sources used

| Model | Original Step 65 weight | Used Step 66 weight | Files |
|---|---:|---:|---|
| v41 — последни прогнозни сигнали | 0.259067 | 0.290698 | models/v41/v41_latest_predictions.json<br>models/v41/v41_frequency_main_numbers_model.json<br>models/v41/v41_recency_main_numbers_model.json<br>reports/v41_bst_official_archive_audit.json<br>reports/v41_canonical_draw_events_audit.json<br>reports/v41_model_retraining_summary.json<br>reports/v41_training_readiness_audit.json<br>models/v41/v41_sgd_number_model_metadata.json |
| v44.1 — финален комбиниран анализ комбинация | 0.204663 | 0.229651 | reports/v44_1_final_ensemble_number_scores.csv<br>reports/v44_1_final_ensemble_ticket_summary.json<br>models/v44_1/v44_1_final_ensemble_number_scores.json<br>models/v44_1/v44_1_final_ensemble_ticket_prediction.json |
| v42 — комбиниран позитивен/негативен модел | 0.155440 | 0.174418 | models/v42/v42_combined_prediction.json<br>reports/v42_combined_positive_negative_scores.csv<br>reports/v42_combined_positive_negative_summary.json<br>models/v42/v42_positive_negative_number_scores.json |
| v45 — Prediction Dashboard Pro | 0.054404 | 0.061046 | models/v45/v45_final_prediction_tickets.json<br>reports/v45_training_summary.json<br>models/v45/v45_latest_number_scores.json<br>models/v45/v45_model_metadata.json |
| v51 — пакет от комбинации | 0.054404 | 0.061046 | reports/v51_current_pro_ticket_score.csv |
| v57 — горещи, студени и стабилни | 0.054404 | 0.061046 | reports/v57_hot_cold_stable_numbers.csv<br>reports/v57_hot_cold_stable_numbers.json<br>reports/v57_hot_cold_stable_summary.json |
| v58 — обединена оценка | 0.054404 | 0.061046 | reports/v58_smart_ensemble_scores_sample.csv<br>reports/v58_smart_ensemble_scores_sample.json |
| v59 — интелигентен генератор 2 | 0.054404 | 0.061046 | reports/v59_smart_ticket_builder_2_summary.json<br>reports/v59_smart_ticket_builder_2_sample.csv<br>reports/v59_smart_ticket_builder_2_sample.json |

## Top weighted numbers

| Rank | Number | Претеглена оценка % | Source count | Status |
|---:|---:|---:|---:|---|
| 1 | 1 | 100.0% | 7 | водещ претеглен сигнал |
| 2 | 2 | 98.108% | 8 | водещ претеглен сигнал |
| 3 | 37 | 87.683% | 6 | водещ претеглен сигнал |
| 4 | 38 | 85.871% | 6 | водещ претеглен сигнал |
| 5 | 4 | 84.348% | 8 | водещ претеглен сигнал |
| 6 | 18 | 79.854% | 7 | водещ претеглен сигнал |
| 7 | 21 | 79.029% | 8 | водещ претеглен сигнал |
| 8 | 22 | 78.744% | 6 | водещ претеглен сигнал |
| 9 | 49 | 78.704% | 6 | водещ претеглен сигнал |
| 10 | 34 | 73.587% | 8 | силен потвърден сигнал |
| 11 | 23 | 73.379% | 5 | силен потвърден сигнал |
| 12 | 44 | 72.642% | 7 | силен потвърден сигнал |
| 13 | 13 | 58.193% | 7 | балансиран сигнал |
| 14 | 3 | 57.62% | 7 | балансиран сигнал |
| 15 | 17 | 55.799% | 8 | балансиран сигнал |

## Reference combinations

These are референтни комбинации built from weighted statistical signals. They are not гаранция за печалбаs.

- Ticket 1: 1, 2, 4, 18, 37, 38
- Ticket 2: 2, 3, 4, 22, 23, 48
- Ticket 3: 16, 17, 18, 37, 44, 49
- Ticket 4: 11, 13, 21, 34, 38, 42

## Skipped sources

- v50_pair_group_intelligence: no parseable score source files found
- v61_latest_draw_signal_hits: post-draw analyzer; used for reliability context, not direct score source
