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
| v44.1 — финална обединена комбинация | 0.200340 | 0.227368 | reports/v44_1_final_ensemble_number_scores.csv<br>reports/v44_1_final_ensemble_ticket_summary.json<br>models/v44_1/v44_1_final_ensemble_number_scores.json<br>models/v44_1/v44_1_final_ensemble_ticket_prediction.json |
| v41 — последни прогнозни сигнали | 0.185735 | 0.210792 | models/v41/v41_latest_predictions.json<br>models/v41/v41_frequency_main_numbers_model.json<br>models/v41/v41_recency_main_numbers_model.json<br>reports/v41_bst_official_archive_audit.json<br>reports/v41_canonical_draw_events_audit.json<br>reports/v41_model_retraining_summary.json<br>reports/v41_training_readiness_audit.json<br>models/v41/v41_sgd_number_model_metadata.json |
| v42 — комбиниран позитивен/негативен модел | 0.180339 | 0.204668 | models/v42/v42_combined_prediction.json<br>reports/v42_combined_positive_negative_scores.csv<br>reports/v42_combined_positive_negative_summary.json<br>models/v42/v42_positive_negative_number_scores.json |
| v45 — Prediction Dashboard Pro | 0.076966 | 0.087349 | models/v45/v45_final_prediction_tickets.json<br>reports/v45_training_summary.json<br>models/v45/v45_latest_number_scores.json<br>models/v45/v45_model_metadata.json |
| v51 — пакет от комбинации | 0.059437 | 0.067456 | reports/v51_current_pro_ticket_score.csv |
| v57 — горещи, студени и стабилни | 0.059437 | 0.067456 | reports/v57_hot_cold_stable_numbers.csv<br>reports/v57_hot_cold_stable_numbers.json<br>reports/v57_hot_cold_stable_summary.json |
| v58 — обединена оценка | 0.059437 | 0.067456 | reports/v58_smart_ensemble_scores_sample.csv<br>reports/v58_smart_ensemble_scores_sample.json |
| v59 — интелигентен генератор 2 | 0.059437 | 0.067456 | reports/v59_smart_ticket_builder_2_summary.json<br>reports/v59_smart_ticket_builder_2_sample.csv<br>reports/v59_smart_ticket_builder_2_sample.json |

## Top weighted numbers

| Rank | Number | Претеглена оценка % | Source count | Status |
|---:|---:|---:|---:|---|
| 1 | 1 | 100.0% | 7 | водещ претеглен сигнал |
| 2 | 2 | 96.664% | 7 | водещ претеглен сигнал |
| 3 | 37 | 88.682% | 6 | водещ претеглен сигнал |
| 4 | 11 | 81.848% | 7 | водещ претеглен сигнал |
| 5 | 38 | 78.864% | 7 | водещ претеглен сигнал |
| 6 | 22 | 75.323% | 8 | водещ претеглен сигнал |
| 7 | 4 | 75.262% | 7 | водещ претеглен сигнал |
| 8 | 21 | 75.183% | 6 | водещ претеглен сигнал |
| 9 | 18 | 73.298% | 5 | силен потвърден сигнал |
| 10 | 23 | 72.382% | 5 | силен потвърден сигнал |
| 11 | 44 | 71.212% | 8 | силен потвърден сигнал |
| 12 | 34 | 68.374% | 6 | силен потвърден сигнал |
| 13 | 42 | 64.116% | 8 | силен потвърден сигнал |
| 14 | 17 | 60.615% | 8 | силен потвърден сигнал |
| 15 | 16 | 58.754% | 6 | балансиран сигнал |

## Reference combinations

These are reference combinations built from weighted statistical signals. They do not guarantee a win.

- Ticket 1: 1, 2, 11, 22, 37, 38
- Ticket 2: 2, 3, 17, 21, 38, 44
- Ticket 3: 16, 18, 22, 34, 37, 43
- Ticket 4: 4, 11, 23, 24, 42, 49

## Skipped sources

- v50_pair_group_intelligence: no parseable score source files found
- v61_latest_draw_signal_hits: post-draw analyzer; used for reliability context, not direct score source
