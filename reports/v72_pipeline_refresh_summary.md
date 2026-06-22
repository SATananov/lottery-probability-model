# Step 72 — Full Weighted Pipeline Refresh Integration

Mode: **run**
Include core: **False**
Steps planned: **10**
All scripts present: **True**
All outputs present: **True**

**Important:** This is a statistical refresh pipeline. It is not a prediction and not a winning guarantee.

## Steps

| Step | Name | Script | Script OK | Outputs OK | Run status |
|---:|---|---|---|---|---|
| 61 | Анализ на нов тираж | `scripts/v61_build_draw_result_analyzer.py` | True | True | OK |
| 62 | История на моделите | `scripts/v62_build_model_performance_tracker.py` | True | True | OK |
| 63 | Надеждност на моделите | `scripts/v63_build_model_reliability_dashboard.py` | True | True | OK |
| 65 | Умно тегло на моделите | `scripts/v65_build_model_weighting_center.py` | True | True | OK |
| 66 | Претеглен ensemble анализ | `scripts/v66_build_weighted_smart_ensemble.py` | True | True | OK |
| 67 | Умен генератор с тегла | `scripts/v67_build_weighted_ticket_builder.py` | True | True | OK |
| 68 | Умен portfolio optimizer | `scripts/v68_build_weighted_portfolio_optimizer.py` | True | True | OK |
| 69 | Подобряване на портфолио | `scripts/v69_build_portfolio_improvement_suggestions.py` | True | True | OK |
| 70 | Приложен подобрен портфейл | `scripts/v70_build_applied_candidate_portfolio.py` | True | True | OK |
| 71 | Пакет за игра | `scripts/v71_build_ticket_pack_export.py` | True | True | OK |
