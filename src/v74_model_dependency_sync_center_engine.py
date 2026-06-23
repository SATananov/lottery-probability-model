from __future__ import annotations

from pathlib import Path
import csv
import json
import hashlib
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V74_MODELS_DIR = MODELS_DIR / "v74"

SUMMARY_PATH = REPORTS_DIR / "v74_model_dependency_summary.json"
SUMMARY_MD_PATH = REPORTS_DIR / "v74_model_dependency_summary.md"
MAP_PATH = REPORTS_DIR / "v74_model_dependency_map.csv"
STATUS_PATH = REPORTS_DIR / "v74_model_sync_status.csv"
REGISTRY_PATH = MODELS_DIR / "model_registry.json"
MODEL_PATH = V74_MODELS_DIR / "v74_model_dependency_sync_center_model.json"

SAFE_NOTE = (
    "Step 74 е контролен слой за синхрон между набори данни, модели, отчети и стъпки от веригата. "
    "Той не е прогноза и не е гаранция за печалба."
)

PRIMARY_DATASETS = [
    "data/historical_draws.csv",
    "data/v40_normalized_draw_events.csv",
    "data/v41_canonical_draw_events.csv",
]

MODEL_NODES: list[dict[str, Any]] = json.loads(r'''
[
  {
    "step": "41",
    "label": "\u041f\u0440\u0430\u0432\u0438\u043b\u043e\u0432\u043e-\u0441\u044a\u0437\u043d\u0430\u0442\u0438 \u043c\u043e\u0434\u0435\u043b\u0438",
    "category": "\u0411\u0430\u0437\u043e\u0432 \u043c\u043e\u0434\u0435\u043b",
    "script": "scripts/v41_train_rules_aware_models.py",
    "datasets": [
      "data/v41_canonical_draw_events.csv"
    ],
    "inputs": [
      "data/v41_canonical_draw_events.csv"
    ],
    "outputs": [
      "models/v41/v41_latest_predictions.json",
      "reports/v41_model_retraining_summary.json"
    ],
    "feeds": [
      "Step 62",
      "Step 65",
      "Step 66"
    ],
    "role": "\u0414\u0430\u0432\u0430 \u043f\u0440\u0430\u0432\u0438\u043b\u0430-\u0441\u0432\u044a\u0440\u0437\u0430\u043d\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438 \u0432\u044a\u0440\u0445\u0443 \u043e\u0441\u043d\u043e\u0432\u043d\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430.",
    "ensemble_source": true
  },
  {
    "step": "42",
    "label": "\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u043f\u043e\u0437\u0438\u0442\u0438\u0432\u0435\u043d/\u043d\u0435\u0433\u0430\u0442\u0438\u0432\u0435\u043d \u0430\u043d\u0430\u043b\u0438\u0437",
    "category": "\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0430\u043d\u0430\u043b\u0438\u0437",
    "script": "scripts/v42_build_combined_positive_negative_foundation.py",
    "datasets": [
      "data/v41_canonical_draw_events.csv"
    ],
    "inputs": [
      "data/v41_canonical_draw_events.csv"
    ],
    "outputs": [
      "models/v42/v42_combined_prediction.json",
      "reports/v42_combined_positive_negative_summary.json"
    ],
    "feeds": [
      "Step 62",
      "Step 65",
      "Step 66"
    ],
    "role": "\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430 \u043f\u043e\u0437\u0438\u0442\u0438\u0432\u043d\u0438 \u0438 \u043d\u0435\u0433\u0430\u0442\u0438\u0432\u043d\u0438 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438.",
    "ensemble_source": true
  },
  {
    "step": "43.1",
    "label": "\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u0440\u0438\u0442\u044a\u043c",
    "category": "\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u0430\u043d\u0430\u043b\u0438\u0437",
    "script": "scripts/v43_1_refine_interval_rhythm_foundation.py",
    "datasets": [
      "data/v41_canonical_draw_events.csv"
    ],
    "inputs": [
      "data/v41_canonical_draw_events.csv"
    ],
    "outputs": [
      "models/v43_1/v43_1_interval_rhythm_refined_prediction.json",
      "reports/v43_1_interval_rhythm_refined_summary.json"
    ],
    "feeds": [
      "Step 44.1",
      "Step 58"
    ],
    "role": "\u0421\u043b\u0435\u0434\u0438 \u0440\u0438\u0442\u044a\u043c \u043d\u0430 \u043f\u043e\u044f\u0432\u0430, \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0438 \u0438 \u0437\u0430\u043a\u044a\u0441\u043d\u0435\u043b\u0438 \u0447\u0438\u0441\u043b\u0430.",
    "ensemble_source": false
  },
  {
    "step": "44.1",
    "label": "\u0424\u0438\u043d\u0430\u043b\u043d\u0430 \u0430\u043d\u0441\u0430\u043c\u0431\u043b\u043e\u0432\u0430 \u043e\u0441\u043d\u043e\u0432\u0430 \u0437\u0430 \u0444\u0438\u0448",
    "category": "\u0410\u043d\u0441\u0430\u043c\u0431\u044a\u043b",
    "script": "scripts/v44_1_refine_final_ensemble_ticket_foundation.py",
    "datasets": [
      "data/v41_canonical_draw_events.csv"
    ],
    "inputs": [
      "models/v42/v42_combined_prediction.json",
      "models/v43_1/v43_1_interval_rhythm_refined_prediction.json"
    ],
    "outputs": [
      "models/v44_1/v44_1_final_ensemble_ticket_prediction.json",
      "reports/v44_1_final_ensemble_ticket_summary.json"
    ],
    "feeds": [
      "Step 62",
      "Step 65",
      "Step 66"
    ],
    "role": "\u041e\u0431\u0435\u0434\u0438\u043d\u044f\u0432\u0430 \u043f\u043e-\u0440\u0430\u043d\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438 \u0432\u044a\u0432 \u0444\u0438\u043d\u0430\u043b\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u043b\u043e\u0432 \u0444\u0438\u0448.",
    "ensemble_source": true
  },
  {
    "step": "45",
    "label": "\u041f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u043e \u0442\u0430\u0431\u043b\u043e Pro",
    "category": "ML \u043c\u043e\u0434\u0435\u043b",
    "script": "scripts/v45_train_prediction_engine_pro.py",
    "datasets": [
      "data/v41_canonical_draw_events.csv"
    ],
    "inputs": [
      "data/v41_canonical_draw_events.csv"
    ],
    "outputs": [
      "models/v45/v45_model_metadata.json",
      "reports/v45_training_summary.json"
    ],
    "feeds": [
      "Step 62",
      "Step 65",
      "Step 66"
    ],
    "role": "\u0422\u0440\u0435\u043d\u0438\u0440\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u043c\u043e\u0434\u0435\u043b \u0441 \u043f\u0440\u0438\u0437\u043d\u0430\u0446\u0438 \u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430.",
    "ensemble_source": true
  },
  {
    "step": "50",
    "label": "\u0410\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u0434\u0432\u043e\u0439\u043a\u0438 \u0438 \u0433\u0440\u0443\u043f\u0438",
    "category": "\u0413\u0440\u0443\u043f\u043e\u0432\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430",
    "script": "scripts/v50_build_pair_group_intelligence.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "data/historical_draws.csv"
    ],
    "outputs": [
      "models/v50/v50_pair_group_intelligence.json",
      "reports/v50_pair_group_summary.json"
    ],
    "feeds": [
      "Step 51",
      "Step 62",
      "Step 65"
    ],
    "role": "\u0410\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u0430 \u0434\u0432\u043e\u0439\u043a\u0438, \u0433\u0440\u0443\u043f\u0438 \u0438 \u0441\u044a\u0432\u043c\u0435\u0441\u0442\u043d\u0438 \u043f\u043e\u044f\u0432\u0438.",
    "ensemble_source": false
  },
  {
    "step": "51",
    "label": "\u0418\u043d\u0442\u0435\u043b\u0438\u0433\u0435\u043d\u0442\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430 \u043d\u0430 \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b \u043e\u0442 \u0444\u0438\u0448\u043e\u0432\u0435",
    "category": "\u041f\u043e\u0440\u0442\u0444\u043e\u043b\u0438\u043e",
    "script": "scripts/v51_build_ticket_portfolio_intelligence.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "models/v50/v50_pair_group_intelligence.json",
      "data/historical_draws.csv"
    ],
    "outputs": [
      "models/v51/v51_ticket_portfolio_intelligence.json",
      "reports/v51_ticket_portfolio_summary.json"
    ],
    "feeds": [
      "Step 62",
      "Step 65",
      "Step 66"
    ],
    "role": "\u041e\u0446\u0435\u043d\u044f\u0432\u0430 \u0444\u0438\u0448\u043e\u0432\u0435 \u0438 \u043f\u043e\u0440\u0442\u0444\u043e\u043b\u0438\u043e \u0447\u0440\u0435\u0437 \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435 \u0438 \u0433\u0440\u0443\u043f\u043e\u0432\u0430 \u043b\u043e\u0433\u0438\u043a\u0430.",
    "ensemble_source": true
  },
  {
    "step": "55",
    "label": "\u041f\u0440\u043e\u0444\u0438\u043b \u043d\u0430 \u0447\u0438\u0441\u043b\u043e",
    "category": "\u041f\u0440\u043e\u0444\u0438\u043b\u0438\u0440\u0430\u043d\u0435",
    "script": "scripts/v55_build_number_profile_center.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "data/historical_draws.csv"
    ],
    "outputs": [
      "models/v55/v55_number_profile_manifest.json",
      "reports/v55_number_profile_summary.json"
    ],
    "feeds": [
      "Step 56",
      "Step 57",
      "Step 58"
    ],
    "role": "\u041f\u0440\u043e\u0444\u0438\u043b\u0438\u0440\u0430 \u0432\u0441\u044f\u043a\u043e \u0447\u0438\u0441\u043b\u043e \u043f\u043e \u0447\u0435\u0441\u0442\u043e\u0442\u0430, \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0438, \u0434\u0432\u043e\u0439\u043a\u0438 \u0438 \u0441\u0442\u0430\u0431\u0438\u043b\u043d\u043e\u0441\u0442.",
    "ensemble_source": false
  },
  {
    "step": "56",
    "label": "\u041f\u043e\u0434\u043e\u0431\u043d\u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0442\u0438\u0440\u0430\u0436\u0438",
    "category": "\u0421\u0445\u043e\u0434\u0441\u0442\u0432\u0430",
    "script": "scripts/v56_build_draw_similarity_search.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "data/historical_draws.csv",
      "reports/v55_number_profiles.json"
    ],
    "outputs": [
      "models/v56/v56_draw_similarity_manifest.json",
      "reports/v56_draw_similarity_summary.json"
    ],
    "feeds": [
      "UI \u0430\u043d\u0430\u043b\u0438\u0437"
    ],
    "role": "\u0422\u044a\u0440\u0441\u0438 \u0441\u0445\u043e\u0434\u043d\u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0442\u0438\u0440\u0430\u0436\u0438 \u0438 \u043c\u043e\u0434\u0435\u043b\u0438 \u043d\u0430 \u0431\u043b\u0438\u0437\u043e\u0441\u0442.",
    "ensemble_source": false
  },
  {
    "step": "57",
    "label": "\u0413\u043e\u0440\u0435\u0449\u0438, \u0441\u0442\u0443\u0434\u0435\u043d\u0438 \u0438 \u0441\u0442\u0430\u0431\u0438\u043b\u043d\u0438 \u0447\u0438\u0441\u043b\u0430",
    "category": "\u0413\u043e\u0440\u0435\u0449\u0438/\u0441\u0442\u0443\u0434\u0435\u043d\u0438 \u0447\u0438\u0441\u043b\u0430",
    "script": "scripts/v57_build_hot_cold_stable_center.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "data/historical_draws.csv",
      "reports/v55_number_profile_summary.json"
    ],
    "outputs": [
      "models/v57/v57_hot_cold_stable_manifest.json",
      "reports/v57_hot_cold_stable_summary.json"
    ],
    "feeds": [
      "Step 58",
      "Step 62",
      "Step 65",
      "Step 66"
    ],
    "role": "\u041e\u0442\u043a\u0440\u0438\u0432\u0430 \u0433\u043e\u0440\u0435\u0449\u0438, \u0441\u0442\u0443\u0434\u0435\u043d\u0438 \u0438 \u0441\u0442\u0430\u0431\u0438\u043b\u043d\u0438 \u0447\u0438\u0441\u043b\u0430.",
    "ensemble_source": true
  },
  {
    "step": "58",
    "label": "\u0423\u043c\u043d\u0430 \u043e\u0431\u0435\u0434\u0438\u043d\u0435\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430 2",
    "category": "\u0423\u043c\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b",
    "script": "scripts/v58_build_smart_ensemble_score_2.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "models/v57/v57_hot_cold_stable_manifest.json",
      "reports/v55_number_profile_summary.json"
    ],
    "outputs": [
      "models/v58/v58_smart_ensemble_manifest.json",
      "reports/v58_smart_ensemble_summary.json"
    ],
    "feeds": [
      "Step 59",
      "Step 62",
      "Step 65",
      "Step 66"
    ],
    "role": "\u041e\u0431\u0435\u0434\u0438\u043d\u044f\u0432\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438 \u0432 \u0438\u043d\u0442\u0435\u043b\u0438\u0433\u0435\u043d\u0442\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430.",
    "ensemble_source": true
  },
  {
    "step": "59",
    "label": "\u0423\u043c\u0435\u043d \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u043d\u0430 \u0444\u0438\u0448\u043e\u0432\u0435 2",
    "category": "\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440",
    "script": "scripts/v59_build_smart_ticket_builder_2.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v58_smart_ensemble_scores_sample.json"
    ],
    "outputs": [
      "models/v59/v59_smart_ticket_builder_2_manifest.json",
      "reports/v59_smart_ticket_builder_2_summary.json"
    ],
    "feeds": [
      "Step 60",
      "Step 62",
      "Step 65"
    ],
    "role": "\u0413\u0435\u043d\u0435\u0440\u0438\u0440\u0430 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u043f\u043e \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u0438 \u0441\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u0438.",
    "ensemble_source": true
  },
  {
    "step": "61",
    "label": "\u0410\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u043d\u043e\u0432 \u0442\u0438\u0440\u0430\u0436",
    "category": "\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0441\u043b\u0435\u0434 \u0442\u0438\u0440\u0430\u0436",
    "script": "scripts/v61_build_draw_result_analyzer.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "data/historical_draws.csv",
      "models/v41/v41_latest_predictions.json",
      "reports/v58_smart_ensemble_scores_sample.json"
    ],
    "outputs": [
      "models/v61/v61_draw_result_analyzer_manifest.json",
      "reports/v61_draw_result_analyzer_summary.json"
    ],
    "feeds": [
      "Step 62",
      "Step 63"
    ],
    "role": "\u041f\u0440\u043e\u0432\u0435\u0440\u044f\u0432\u0430 \u0441\u0438\u0433\u043d\u0430\u043b\u0438\u0442\u0435 \u0441\u0440\u0435\u0449\u0443 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u044f \u0440\u0435\u0430\u043b\u0435\u043d \u0442\u0438\u0440\u0430\u0436.",
    "ensemble_source": false
  },
  {
    "step": "62",
    "label": "\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435",
    "category": "\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043d\u0430 \u043f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u044f\u043d\u0435\u0442\u043e",
    "script": "scripts/v62_build_model_performance_tracker.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v61_draw_result_analyzer_summary.json"
    ],
    "outputs": [
      "models/v62/v62_model_performance_tracker_model.json",
      "reports/v62_model_performance_summary.json"
    ],
    "feeds": [
      "Step 63"
    ],
    "role": "\u0421\u044a\u0431\u0438\u0440\u0430 \u0438\u0441\u0442\u043e\u0440\u0438\u044f \u043d\u0430 \u043f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u044f\u043d\u0435\u0442\u043e \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435.",
    "ensemble_source": false
  },
  {
    "step": "63",
    "label": "\u041d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435",
    "category": "\u041d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442",
    "script": "scripts/v63_build_model_reliability_dashboard.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v62_model_performance_summary.json"
    ],
    "outputs": [
      "models/v63/v63_model_reliability_dashboard_model.json",
      "reports/v63_model_reliability_summary.json",
      "reports/v63_model_reliability_scores.csv"
    ],
    "feeds": [
      "Step 65"
    ],
    "role": "\u0418\u0437\u0447\u0438\u0441\u043b\u044f\u0432\u0430 \u043e\u0446\u0435\u043d\u043a\u0430 \u0437\u0430 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442 \u043d\u0430 \u0441\u043b\u0435\u0434\u0435\u043d\u0438\u0442\u0435 \u043c\u043e\u0434\u0435\u043b\u0438.",
    "ensemble_source": false
  },
  {
    "step": "65",
    "label": "\u0423\u043c\u043d\u043e \u0442\u0435\u0433\u043b\u043e \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435",
    "category": "\u0410\u0434\u0430\u043f\u0442\u0438\u0432\u043d\u043e \u0442\u0435\u0433\u043b\u043e",
    "script": "scripts/v65_build_model_weighting_center.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v63_model_reliability_scores.csv"
    ],
    "outputs": [
      "models/v65/v65_model_weighting_center_model.json",
      "reports/v65_model_weighting_summary.json",
      "reports/v65_model_weights.csv"
    ],
    "feeds": [
      "Step 66"
    ],
    "role": "\u041f\u0440\u0435\u0432\u0440\u044a\u0449\u0430 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442\u0442\u0430 \u0432 \u0430\u0434\u0430\u043f\u0442\u0438\u0432\u043d\u0438 \u0442\u0435\u0433\u043b\u0430.",
    "ensemble_source": false
  },
  {
    "step": "66",
    "label": "\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u043b\u043e\u0432 \u0430\u043d\u0430\u043b\u0438\u0437",
    "category": "\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b",
    "script": "scripts/v66_build_weighted_smart_ensemble.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v65_model_weights.csv"
    ],
    "outputs": [
      "models/v66/v66_weighted_smart_ensemble_model.json",
      "reports/v66_weighted_smart_ensemble_summary.json",
      "reports/v66_weighted_smart_ensemble_scores.csv"
    ],
    "feeds": [
      "Step 67",
      "Step 68",
      "Step 69"
    ],
    "role": "\u041e\u0431\u0435\u0434\u0438\u043d\u044f\u0432\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0442\u0435 \u0441\u0438\u0433\u043d\u0430\u043b\u0438 \u0441\u043f\u043e\u0440\u0435\u0434 \u0430\u0434\u0430\u043f\u0442\u0438\u0432\u043d\u0438\u0442\u0435 \u0442\u0435\u0433\u043b\u0430.",
    "ensemble_source": false
  },
  {
    "step": "67",
    "label": "\u0423\u043c\u0435\u043d \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u0441 \u0442\u0435\u0433\u043b\u0430",
    "category": "\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u0441 \u0442\u0435\u0433\u043b\u0430",
    "script": "scripts/v67_build_weighted_ticket_builder.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v66_weighted_smart_ensemble_scores.csv"
    ],
    "outputs": [
      "models/v67/v67_weighted_ticket_builder_model.json",
      "reports/v67_weighted_ticket_builder_summary.json",
      "reports/v67_weighted_ticket_builder_tickets.csv"
    ],
    "feeds": [
      "Step 68"
    ],
    "role": "\u0421\u0442\u0440\u043e\u0438 \u0444\u0438\u0448\u043e\u0432\u0435 \u0432\u044a\u0440\u0445\u0443 \u043f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d\u0438\u0442\u0435 \u043e\u0446\u0435\u043d\u043a\u0438 \u043e\u0442 Step 66.",
    "ensemble_source": false
  },
  {
    "step": "68",
    "label": "\u0423\u043c\u0435\u043d \u043e\u043f\u0442\u0438\u043c\u0438\u0437\u0430\u0442\u043e\u0440 \u043d\u0430 \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b",
    "category": "\u041e\u043f\u0442\u0438\u043c\u0438\u0437\u0430\u0442\u043e\u0440 \u043d\u0430 \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b",
    "script": "scripts/v68_build_weighted_portfolio_optimizer.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v67_weighted_ticket_builder_tickets.csv",
      "reports/v66_weighted_smart_ensemble_scores.csv"
    ],
    "outputs": [
      "models/v68/v68_weighted_portfolio_optimizer_model.json",
      "reports/v68_weighted_portfolio_summary.json",
      "reports/v68_weighted_portfolio_tickets.csv"
    ],
    "feeds": [
      "Step 69"
    ],
    "role": "\u041e\u0446\u0435\u043d\u044f\u0432\u0430 \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b, \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435, \u043f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u0438\u044f \u0438 \u043a\u043e\u043d\u0446\u0435\u043d\u0442\u0440\u0430\u0446\u0438\u044f.",
    "ensemble_source": false
  },
  {
    "step": "69",
    "label": "\u041f\u043e\u0434\u043e\u0431\u0440\u044f\u0432\u0430\u043d\u0435 \u043d\u0430 \u043f\u043e\u0440\u0442\u0444\u043e\u043b\u0438\u043e",
    "category": "\u041f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u0437\u0430 \u043f\u043e\u0434\u043e\u0431\u0440\u0435\u043d\u0438\u0435",
    "script": "scripts/v69_build_portfolio_improvement_suggestions.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v68_weighted_portfolio_summary.json",
      "reports/v66_weighted_smart_ensemble_scores.csv"
    ],
    "outputs": [
      "models/v69/v69_portfolio_improvement_model.json",
      "reports/v69_portfolio_improvement_summary.json",
      "reports/v69_candidate_portfolio_tickets.csv"
    ],
    "feeds": [
      "Step 70"
    ],
    "role": "\u041f\u0440\u0435\u0434\u043b\u0430\u0433\u0430 \u043f\u043e\u0434\u043e\u0431\u0440\u0435\u043d\u0438\u044f \u0431\u0435\u0437 \u0434\u0430 \u043f\u0440\u0435\u0437\u0430\u043f\u0438\u0441\u0432\u0430 \u043e\u0441\u043d\u043e\u0432\u043d\u0438\u044f \u043f\u0430\u043a\u0435\u0442.",
    "ensemble_source": false
  },
  {
    "step": "70",
    "label": "\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d \u043f\u043e\u0434\u043e\u0431\u0440\u0435\u043d \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b",
    "category": "\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b",
    "script": "scripts/v70_build_applied_candidate_portfolio.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v69_candidate_portfolio_tickets.csv"
    ],
    "outputs": [
      "models/v70/v70_applied_candidate_portfolio_model.json",
      "reports/v70_applied_candidate_portfolio_summary.json",
      "reports/v70_applied_candidate_portfolio_tickets.csv"
    ],
    "feeds": [
      "Step 71"
    ],
    "role": "\u0424\u0438\u043a\u0441\u0438\u0440\u0430 \u043f\u043e\u0434\u043e\u0431\u0440\u0435\u043d\u0438\u044f \u043f\u0430\u043a\u0435\u0442 \u043a\u0430\u0442\u043e \u043e\u0442\u0434\u0435\u043b\u043d\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0430 \u0440\u0435\u0444\u0435\u0440\u0435\u043d\u0446\u0438\u044f.",
    "ensemble_source": false
  },
  {
    "step": "71",
    "label": "\u041f\u0430\u043a\u0435\u0442 \u0437\u0430 \u0438\u0433\u0440\u0430",
    "category": "\u041f\u0430\u043a\u0435\u0442 \u0437\u0430 \u0438\u0433\u0440\u0430",
    "script": "scripts/v71_build_ticket_pack_export.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v70_applied_candidate_portfolio_tickets.csv"
    ],
    "outputs": [
      "models/v71/v71_ticket_pack_export_model.json",
      "reports/v71_ticket_pack_summary.json",
      "reports/v71_ticket_pack.csv"
    ],
    "feeds": [
      "Step 73"
    ],
    "role": "\u041f\u043e\u0434\u0433\u043e\u0442\u0432\u044f \u043f\u0430\u043a\u0435\u0442 \u0437\u0430 \u043f\u0435\u0447\u0430\u0442 \u0438 \u0435\u043a\u0441\u043f\u043e\u0440\u0442 \u0437\u0430 \u0438\u0433\u0440\u0430 \u0441 \u0444\u0438\u0437\u0438\u0447\u0435\u0441\u043a\u0438 \u0444\u0438\u0448\u043e\u0432\u0435.",
    "ensemble_source": false
  },
  {
    "step": "73",
    "label": "\u041f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u044f\u043d\u0435 \u043d\u0430 \u043f\u0430\u043a\u0435\u0442\u0430",
    "category": "\u041f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u044f\u043d\u0435 \u0441\u043b\u0435\u0434 \u0442\u0438\u0440\u0430\u0436",
    "script": "scripts/v73_build_ticket_pack_performance_tracker.py",
    "datasets": [
      "data/historical_draws.csv"
    ],
    "inputs": [
      "reports/v71_ticket_pack.csv"
    ],
    "outputs": [
      "models/v73/v73_ticket_pack_performance_tracker_model.json",
      "reports/v73_ticket_pack_performance_summary.json",
      "reports/v73_ticket_pack_performance_history.csv"
    ],
    "feeds": [
      "Step 75"
    ],
    "role": "\u041f\u0440\u043e\u0432\u0435\u0440\u044f\u0432\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u044f \u043f\u0430\u043a\u0435\u0442 \u0441\u0440\u0435\u0449\u0443 \u0440\u0435\u0430\u043b\u043d\u0438 \u0442\u0438\u0440\u0430\u0436\u0438 \u043f\u0440\u0435\u0434\u0438 \u043e\u0431\u043d\u043e\u0432\u044f\u0432\u0430\u043d\u0435 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435.",
    "ensemble_source": false
  },
  {
    "step": "75",
    "label": "\u041d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u043c\u0435\u0442\u0430-\u043e\u0431\u0443\u0447\u0438\u0442\u0435\u043b",
    "category": "\u041d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u043c\u0435\u0442\u0430-\u043e\u0431\u0443\u0447\u0438\u0442\u0435\u043b",
    "script": "scripts/v75_build_neural_meta_learner.py",
    "datasets": [
      "data/v41_canonical_draw_events.csv",
      "data/historical_draws.csv"
    ],
    "inputs": [
      "data/v41_canonical_draw_events.csv"
    ],
    "outputs": [
      "models/v75/v75_neural_meta_learner_model.json",
      "reports/v75_neural_meta_learner_summary.json",
      "reports/v75_neural_meta_number_scores.csv",
      "reports/v75_neural_candidate_tickets.csv",
      "reports/v75_neural_candidate_tickets.json"
    ],
    "feeds": [
      "Step 74"
    ],
    "role": "\u0422\u0440\u0435\u043d\u0438\u0440\u0430 \u043b\u0435\u043a \u043d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u043c\u0435\u0442\u0430-\u043e\u0431\u0443\u0447\u0438\u0442\u0435\u043b \u0432\u044a\u0440\u0445\u0443 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u0446\u0438 \u0438 \u0438\u0437\u0433\u0440\u0430\u0436\u0434\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442 \u0444\u0438\u0448\u043e\u0432\u0435.",
    "ensemble_source": false
  }
]
''')



def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_text_if_changed(path: Path, content: str, encoding: str = "utf-8") -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            if path.read_text(encoding=encoding) == content:
                return False
        except UnicodeError:
            pass
    path.write_text(content, encoding=encoding)
    return True


def _stable_json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def _state_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    import io

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    content = "\ufeff" + output.getvalue()
    _write_text_if_changed(path, content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    _write_text_if_changed(path, _stable_json_text(data) + "\n", encoding="utf-8")


def rel_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def rel_mtime(rel_path: str) -> float:
    path = ROOT / rel_path
    if not path.exists():
        return 0.0
    return path.stat().st_mtime


def rel_mtime_iso(rel_path: str) -> str:
    ts = rel_mtime(rel_path)
    if not ts:
        return ""
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def max_mtime(paths: list[str]) -> float:
    times = [rel_mtime(path) for path in paths if rel_exists(path)]
    return max(times) if times else 0.0


def dataset_info(rel_path: str) -> dict[str, Any]:
    path = ROOT / rel_path
    rows = read_csv_rows(path)
    info: dict[str, Any] = {
        "path": rel_path,
        "exists": path.exists(),
        "rows": len(rows),
        "latest_date": "",
        "latest_year": "",
        "latest_draw_no": "",
        "latest_numbers": "",
        "mtime": rel_mtime_iso(rel_path),
    }
    if not rows:
        return info

    latest = rows[-1]
    info["latest_date"] = latest.get("date", "")
    info["latest_year"] = latest.get("year", "")
    info["latest_draw_no"] = latest.get("draw_no", latest.get("draw_number", ""))
    numbers = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = str(latest.get(key, "")).strip()
        if value:
            numbers.append(value)
    info["latest_numbers"] = ",".join(numbers)
    return info


def compare_primary_datasets(dataset_infos: list[dict[str, Any]]) -> dict[str, Any]:
    existing = [item for item in dataset_infos if item.get("exists")]
    row_counts = sorted({item.get("rows") for item in existing})
    latest_keys = sorted({
        (item.get("latest_date"), item.get("latest_draw_no"), item.get("latest_numbers"))
        for item in existing
    })
    return {
        "datasets_checked": len(dataset_infos),
        "datasets_existing": len(existing),
        "row_counts": row_counts,
        "latest_draw_signatures": [" | ".join(str(part) for part in key) for key in latest_keys],
        "rows_synced": len(row_counts) == 1 and len(existing) == len(dataset_infos),
        "latest_draw_synced": len(latest_keys) == 1 and len(existing) == len(dataset_infos),
    }


def node_status(node: dict[str, Any]) -> dict[str, Any]:
    script = str(node.get("script", ""))
    outputs = [str(item) for item in node.get("outputs", [])]
    inputs = [str(item) for item in node.get("inputs", [])]
    datasets = [str(item) for item in node.get("datasets", [])]
    dependencies = sorted(set(inputs + datasets))

    script_exists = rel_exists(script)
    missing_inputs = [path for path in dependencies if not rel_exists(path)]
    missing_outputs = [path for path in outputs if not rel_exists(path)]

    latest_input_ts = max_mtime(dependencies)
    latest_output_ts = max_mtime(outputs)
    stale = bool(latest_input_ts and latest_output_ts and latest_output_ts + 1 < latest_input_ts)

    if not script_exists or missing_inputs or missing_outputs:
        sync_status = "Липсва файл"
        status_rank = 0
    elif stale:
        sync_status = "Нужно обновяване"
        status_rank = 1
    else:
        sync_status = "Синхронизиран"
        status_rank = 2

    return {
        "step": node.get("step", ""),
        "label": node.get("label", ""),
        "category": node.get("category", ""),
        "script": script,
        "script_exists": script_exists,
        "datasets": "; ".join(datasets),
        "inputs": "; ".join(inputs),
        "outputs": "; ".join(outputs),
        "outputs_present": len(missing_outputs) == 0,
        "dependencies_present": len(missing_inputs) == 0,
        "missing_inputs": "; ".join(missing_inputs),
        "missing_outputs": "; ".join(missing_outputs),
        "latest_input_mtime": datetime.fromtimestamp(latest_input_ts).isoformat(timespec="seconds") if latest_input_ts else "",
        "latest_output_mtime": datetime.fromtimestamp(latest_output_ts).isoformat(timespec="seconds") if latest_output_ts else "",
        "sync_status": sync_status,
        "status_rank": status_rank,
        "feeds": "; ".join(node.get("feeds", [])),
        "role": node.get("role", ""),
        "ensemble_source": bool(node.get("ensemble_source", False)),
        "safe_note": SAFE_NOTE,
    }


def dependency_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in nodes:
        current = f"Step {node.get('step')}"
        for dataset in node.get("datasets", []):
            rows.append({"from": dataset, "to": current, "type": "dataset", "description": "Dataset вход"})
        for dependency in node.get("inputs", []):
            if dependency in node.get("datasets", []):
                continue
            rows.append({"from": dependency, "to": current, "type": "artifact", "description": "Входен model/report artifact"})
        for feed in node.get("feeds", []):
            rows.append({"from": current, "to": feed, "type": "feeds", "description": "Изходът помага на следващ слой"})
    return rows


def build_model_dependency_sync_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V74_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    dataset_infos = [dataset_info(path) for path in PRIMARY_DATASETS]
    dataset_sync = compare_primary_datasets(dataset_infos)
    statuses = [node_status(node) for node in MODEL_NODES]
    edges = dependency_edges(MODEL_NODES)

    synced_count = sum(1 for row in statuses if row["sync_status"] == "Синхронизиран")
    stale_count = sum(1 for row in statuses if row["sync_status"] == "Нужно обновяване")
    missing_count = sum(1 for row in statuses if row["sync_status"] == "Липсва файл")
    ensemble_sources = sum(1 for row in statuses if row.get("ensemble_source"))

    pipeline_chain = [
        "Данни от тиражи",
        "Базови модели и статистики",
        "Историческа проверка и performance",
        "Надеждност на моделите",
        "Адаптивни тегла",
        "Weighted ensemble",
        "Генератор на комбинации",
        "Portfolio optimizer",
        "Пакет за игра",
        "Проверка след реален тираж",
        "Model Dependency & Sync Center",
    ]

    all_synced = dataset_sync["rows_synced"] and dataset_sync["latest_draw_synced"] and missing_count == 0 and stale_count == 0

    summary: dict[str, Any] = {
        "step": "74",
        "name": "Контрол на синхрона между моделите",
        "status": "Синхронизиран" if all_synced else "Има нужда от преглед",
        "all_synced": all_synced,
        "models_checked": len(statuses),
        "synced_models": synced_count,
        "stale_models": stale_count,
        "missing_models": missing_count,
        "ensemble_sources": ensemble_sources,
        "datasets": dataset_infos,
        "dataset_sync": dataset_sync,
        "pipeline_chain": pipeline_chain,
        "generated_at": "",
        "state_hash": "",
        "generated_reports": [
            "reports/v74_model_dependency_summary.json",
            "reports/v74_model_dependency_summary.md",
            "reports/v74_model_dependency_map.csv",
            "reports/v74_model_sync_status.csv",
            "models/model_registry.json",
            "models/v74/v74_model_dependency_sync_center_model.json",
        ],
        "safe_note": SAFE_NOTE,
    }

    stable_payload = {
        "summary_without_runtime": {
            key: value
            for key, value in summary.items()
            if key not in {"generated_at", "state_hash"}
        },
        "sync_status": statuses,
        "dependency_edges": edges,
    }
    state_hash = _state_hash(stable_payload)
    existing_summary = _read_json_if_exists(SUMMARY_PATH)
    if existing_summary.get("state_hash") == state_hash and existing_summary.get("generated_at"):
        generated_at = str(existing_summary.get("generated_at"))
    else:
        generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary["generated_at"] = generated_at
    summary["state_hash"] = state_hash

    registry = {
        "summary": summary,
        "primary_datasets": dataset_infos,
        "models": MODEL_NODES,
        "sync_status": statuses,
        "dependency_edges": edges,
    }

    write_csv(STATUS_PATH, statuses, [
        "step", "label", "category", "script", "script_exists", "datasets", "inputs", "outputs",
        "outputs_present", "dependencies_present", "missing_inputs", "missing_outputs",
        "latest_input_mtime", "latest_output_mtime", "sync_status", "feeds", "role", "ensemble_source", "safe_note",
    ])
    write_csv(MAP_PATH, edges, ["from", "to", "type", "description"])
    write_json(SUMMARY_PATH, summary)
    write_json(REGISTRY_PATH, registry)
    write_json(MODEL_PATH, registry)

    md = [
        "# Step 74 — Контрол на синхрона между моделите",
        "",
        f"Статус: **{summary['status']}**",
        f"Проверени модели/слоеве: **{summary['models_checked']}**",
        f"Синхронизирани: **{summary['synced_models']}**",
        f"Нуждаят се от обновяване: **{summary['stale_models']}**",
        f"Липсващи: **{summary['missing_models']}**",
        f"Ensemble източници: **{summary['ensemble_sources']}**",
        "",
        "**Важно:** Step 74 е контролен и диагностичен слой. Той не е прогноза и не е гаранция за печалба.",
        "",
        "## Dataset синхрон",
        "",
        "| Dataset | Редове | Последна дата | Последен тираж | Последни числа |",
        "|---|---:|---|---|---|",
    ]
    for item in dataset_infos:
        md.append(f"| `{item['path']}` | {item['rows']} | {item['latest_date']} | {item['latest_draw_no']} | {item['latest_numbers']} |")

    md.extend(["", "## Синхрон на моделите", "", "| Step | Име | Категория | Статус | Помага на |", "|---:|---|---|---|---|"])
    for row in statuses:
        md.append(f"| {row['step']} | {row['label']} | {row['category']} | {row['sync_status']} | {row['feeds']} |")

    md.extend(["", "## Логика на веригата", ""])
    for index, item in enumerate(pipeline_chain, start=1):
        md.append(f"{index}. {item}")

    _write_text_if_changed(SUMMARY_MD_PATH, "\n".join(md) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = build_model_dependency_sync_center()
    print("STEP74_BUILD_OK")
    print("STATUS", result.get("status"))
    print("MODELS_CHECKED", result.get("models_checked"))
    print("SYNCED_MODELS", result.get("synced_models"))
    print("STALE_MODELS", result.get("stale_models"))
    print("MISSING_MODELS", result.get("missing_models"))

# STEP 76 EXPLAINABILITY VALIDATION WIRING START
# Added as a safe extension after MODEL_NODES is defined.
_STEP76_NODE = {
    "step": "76",
    "label": "Обяснимост и валидация",
    "category": "Обяснимост и валидация",
    "script": "scripts/v76_build_explainability_validation_center.py",
    "datasets": ["data/v41_canonical_draw_events.csv", "data/historical_draws.csv"],
    "inputs": [
        "reports/v75_neural_meta_number_scores.csv",
        "reports/v75_neural_candidate_tickets.csv",
        "reports/v75_neural_meta_learner_summary.json",
    ],
    "outputs": [
        "models/v76/v76_explainability_validation_model.json",
        "reports/v76_explainability_validation_summary.json",
        "reports/v76_explainability_validation_summary.md",
        "reports/v76_number_explanations.csv",
        "reports/v76_ticket_validation.csv",
        "reports/v76_validation_warnings.csv",
    ],
    "feeds": ["Step 74"],
    "role": "Обяснява Neural Meta Learner сигналите и валидира структурата на кандидат комбинациите преди финалния контрол на синхрона.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "76" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP76_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "75":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 76" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 76" not in _feeds:
            _feeds.append("Step 76")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 76 EXPLAINABILITY VALIDATION WIRING END

# STEP 77 DECISION RECOMMENDATION WIRING START
_STEP77_NODE = {
    "step": "77",
    "label": "Решение и препоръка",
    "category": "Решение и препоръка",
    "script": "scripts/v77_build_decision_recommendation_center.py",
    "datasets": ["data/v41_canonical_draw_events.csv", "data/historical_draws.csv"],
    "inputs": [
        "reports/v76_explainability_validation_summary.json",
        "reports/v76_ticket_validation.csv",
        "reports/v76_number_explanations.csv",
        "reports/v76_validation_warnings.csv",
    ],
    "outputs": [
        "models/v77/v77_decision_recommendation_model.json",
        "reports/v77_decision_recommendation_summary.json",
        "reports/v77_decision_recommendation_summary.md",
        "reports/v77_ticket_recommendations.csv",
        "reports/v77_decision_recommendations.json",
        "reports/v77_decision_warnings.csv",
    ],
    "feeds": ["Step 74"],
    "role": "Обединява обяснимостта и валидацията в практическа статистическа препоръка за кандидат комбинациите.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "77" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP77_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "76":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 77" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 77" not in _feeds:
            _feeds.append("Step 77")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 77 DECISION RECOMMENDATION WIRING END

# STEP 78 FINAL PLAY PLAN WIRING START
_STEP78_NODE = {
    "step": "78",
    "label": "Финален план",
    "category": "Финален план",
    "script": "scripts/v78_build_final_play_plan_center.py",
    "datasets": ["data/v41_canonical_draw_events.csv", "data/historical_draws.csv"],
    "inputs": [
        "reports/v77_decision_recommendation_summary.json",
        "reports/v77_ticket_recommendations.csv",
        "reports/v77_decision_recommendations.json",
        "reports/v77_decision_warnings.csv",
    ],
    "outputs": [
        "models/v78/v78_final_play_plan_model.json",
        "reports/v78_final_play_plan_summary.json",
        "reports/v78_final_play_plan_summary.md",
        "reports/v78_selected_ticket_plan.csv",
        "reports/v78_play_plan_actions.csv",
        "reports/v78_play_plan_warnings.csv",
        "reports/v78_final_play_plan.json",
    ],
    "feeds": ["Step 74"],
    "role": "Превръща decision препоръките във финален дисциплиниран план за основни комбинации, резерви и действия.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "78" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP78_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "77":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 78" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 78" not in _feeds:
            _feeds.append("Step 78")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 78 FINAL PLAY PLAN WIRING END

# STEP 79 TICKET PACK EXPORT WIRING START
_STEP79_NODE = {
    "step": "79",
    "label": "Експорт и изпълнение",
    "category": "Експорт и изпълнение",
    "script": "scripts/v79_build_ticket_pack_export_center.py",
    "datasets": ["data/v41_canonical_draw_events.csv", "data/historical_draws.csv"],
    "inputs": [
        "reports/v78_final_play_plan_summary.json",
        "reports/v78_selected_ticket_plan.csv",
        "reports/v78_play_plan_actions.csv",
        "reports/v78_play_plan_warnings.csv",
    ],
    "outputs": [
        "models/v79/v79_ticket_pack_export_model.json",
        "reports/v79_ticket_pack_export_summary.json",
        "reports/v79_ticket_pack_export_summary.md",
        "reports/v79_export_ticket_pack.csv",
        "reports/v79_execution_checklist.csv",
        "reports/v79_ticket_pack_copy_text.txt",
        "reports/v79_ticket_pack_export.json",
    ],
    "feeds": ["Step 74"],
    "role": "Подготвя финалния пакет за копиране, печат, checklist и дисциплинирано изпълнение.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "79" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP79_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "78":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 79" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 79" not in _feeds:
            _feeds.append("Step 79")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 79 TICKET PACK EXPORT WIRING END

# STEP 80 FINAL SYSTEM AUDIT WIRING START
_STEP80_NODE = {
    "step": "80",
    "label": "Финален системен одит",
    "category": "Финален системен одит",
    "script": "scripts/v80_build_final_system_audit_center.py",
    "datasets": ["data/v41_canonical_draw_events.csv", "data/historical_draws.csv"],
    "inputs": [
        "reports/v79_ticket_pack_export_summary.json",
        "reports/v79_export_ticket_pack.csv",
        "reports/v79_ticket_pack_export.json",
    ],
    "outputs": [
        "models/v80/v80_final_system_audit_model.json",
        "reports/v80_final_system_audit_summary.json",
        "reports/v80_final_system_audit_summary.md",
        "reports/v80_dataset_audit.csv",
        "reports/v80_artifact_audit.csv",
        "reports/v80_file_quality_audit.csv",
        "reports/v80_sync_plan_audit.csv",
    ],
    "feeds": ["Step 74"],
    "role": "Проверява dataset синхрон, Step 76–79 артефакти, sync планове, compile, JSON/CSV parse и кирилица преди финалния sync контрол.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "80" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP80_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "79":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 80" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 80" not in _feeds:
            _feeds.append("Step 80")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 80 FINAL SYSTEM AUDIT WIRING END
# STEP 81 FINAL UX NAVIGATION WIRING START
_STEP81_NODE = {
    "step": "81",
    "label": "Финален UX контрол",
    "category": "Финален UX контрол",
    "script": "scripts/v81_build_final_ux_navigation_center.py",
    "datasets": [],
    "inputs": [
        "streamlit_app.py",
        "reports/v80_final_system_audit_summary.json",
        "reports/v80_sync_plan_audit.csv",
    ],
    "outputs": [
        "models/v81/v81_final_ux_navigation_model.json",
        "reports/v81_final_ux_navigation_summary.json",
        "reports/v81_final_ux_navigation_summary.md",
        "reports/v81_navigation_groups.csv",
        "reports/v81_navigation_page_audit.csv",
        "reports/v81_streamlit_label_audit.csv",
    ],
    "feeds": ["Step 74"],
    "role": "Проверява финалната навигационна структура, групите, повторенията и видимостта на финалните UX labels.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "81" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP81_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "80":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 81" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 81" not in _feeds:
            _feeds.append("Step 81")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 81 FINAL UX NAVIGATION WIRING END
# STEP 82 FINAL RELEASE PACKAGE WIRING START
_STEP82_NODE = {
    "step": "82",
    "label": "Финален пакет за предаване",
    "category": "Финален пакет за предаване",
    "script": "scripts/v82_build_final_release_package_center.py",
    "datasets": [
        "data/historical_draws.csv",
        "data/v40_normalized_draw_events.csv",
        "data/v41_canonical_draw_events.csv",
    ],
    "inputs": [
        "streamlit_app.py",
        "reports/v79_ticket_pack_export_summary.json",
        "reports/v80_final_system_audit_summary.json",
        "reports/v81_final_ux_navigation_summary.json",
    ],
    "outputs": [
        "models/v82/v82_final_release_package_model.json",
        "reports/v82_final_release_summary.json",
        "reports/v82_final_release_summary.md",
        "reports/v82_release_file_manifest.csv",
        "reports/v82_release_readiness_checklist.csv",
        "reports/v82_clean_zip_exclusion_plan.csv",
    ],
    "feeds": ["Step 74"],
    "role": "Финален пакет за предаване readiness и clean ZIP контролен слой след Step 81.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "82" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP82_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "81":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 82" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 82" not in _feeds:
            _feeds.append("Step 82")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 82 FINAL RELEASE PACKAGE WIRING END
# STEP 83 FINAL USER MANUAL WIRING START
_STEP83_NODE = {
    "step": "83",
    "label": "Ръководство за апа",
    "category": "Помощ и ръководство",
    "script": "scripts/v83_build_final_user_manual_center.py",
    "datasets": [
        "data/historical_draws.csv",
        "data/v40_normalized_draw_events.csv",
        "data/v41_canonical_draw_events.csv",
    ],
    "inputs": [
        "streamlit_app.py",
        "reports/v82_final_release_summary.json",
        "reports/v81_final_ux_navigation_summary.json",
        "reports/v79_ticket_pack_export_summary.json",
    ],
    "outputs": [
        "models/v83/v83_final_user_manual_model.json",
        "reports/v83_final_user_manual_summary.json",
        "reports/v83_final_user_manual_summary.md",
        "reports/v83_app_guide_sections.csv",
        "reports/v83_recommended_workflow.csv",
        "reports/v83_safe_usage_checklist.csv",
    ],
    "feeds": ["Step 74"],
    "role": "Финално потребителско ръководство, безопасен работен процес и център с ръководство върху пакета за предаване.",
    "ensemble_source": False,
}

if not any(str(_node.get("step")) == "83" for _node in MODEL_NODES):
    MODEL_NODES.append(_STEP83_NODE)

for _node in MODEL_NODES:
    if str(_node.get("step")) == "82":
        _feeds = [str(_item) for _item in _node.get("feeds", [])]
        _feeds = ["Step 83" if _item == "Step 74" else _item for _item in _feeds]
        if "Step 83" not in _feeds:
            _feeds.append("Step 83")
        _node["feeds"] = [_item for _item in _feeds if _item != "Step 74"]
# STEP 83 FINAL USER MANUAL WIRING END
