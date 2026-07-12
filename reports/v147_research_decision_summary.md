# Step 147 — Experimental Evidence Synthesis & Research Decision Gate

- Decision ID: `DEC-147-0e11bccbcb-46770765b8`
- Source experiments: **3**
- Evidence rows: **9**
- Robust positive rows: **0**
- Robust negative rows: **1**
- Production promotion: **BLOCKED**
- Current neural configuration: **PAUSE_AND_ARCHIVE**

## Decision gate

- PASS — `evidence_chain_complete`
- PASS — `source_statuses_complete`
- PASS — `source_signatures_match`
- PASS — `dataset_identity_consistent`
- PASS — `future_data_leakage_absent`
- PASS — `production_integration_absent`
- FAIL — `robust_superiority_demonstrated`
- FAIL — `all_neural_promotion_gates_passed`

## Evidence matrix

| Step | Candidate | Comparator | Advantage | 95% CI | Outcome |
|---:|---|---|---:|---:|---|
| 144 | frequency_walk_forward | uniform_random_mean | -0.513917 | — | negative |
| 145 | neural_dynamics_reservoir | frequency_walk_forward | -0.087500 | — | negative |
| 145 | neural_dynamics_reservoir | recency_weighted_walk_forward | -0.066667 | — | negative |
| 145 | neural_dynamics_reservoir | uniform_random_mean | -0.092833 | — | negative |
| 146 | neural_dynamics_reservoir | frequency_recency_blend | -0.023333 | [-0.061111, 0.018889] | negative |
| 146 | neural_dynamics_reservoir | frequency_walk_forward | 0.003889 | [-0.041667, 0.052222] | positive_but_not_robust |
| 146 | neural_dynamics_reservoir | recency_weighted_walk_forward | -0.022778 | [-0.057778, 0.010000] | negative |
| 146 | neural_dynamics_reservoir | recent_window_frequency | -0.005000 | [-0.035000, 0.025556] | negative |
| 146 | neural_dynamics_reservoir | uniform_random_mean | -0.061389 | [-0.085944, -0.033056] | robust_negative |

## Decision

No comparison in the Step 144–146 evidence chain demonstrates robust positive superiority. The current neural configuration is therefore paused and archived; production promotion remains blocked.

Следващ експеримент е допустим само при материално нова, предварително регистрирана хипотеза и нов/недокоснат validation период.

Step 147 е research governance слой. Той обобщава исторически експерименти, не прогнозира бъдещи тиражи, не генерира реални фишове и не включва experimental модел в production pipeline.
