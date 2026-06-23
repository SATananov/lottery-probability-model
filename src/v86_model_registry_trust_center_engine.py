from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
import json
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
FALLBACK_DATASET_PATH = ROOT / "data" / "historical_draws.csv"

SUMMARY_PATH = ROOT / "reports" / "v86_model_registry_summary.json"
CSV_PATH = ROOT / "reports" / "v86_model_registry_models.csv"
MD_PATH = ROOT / "reports" / "v86_model_registry_summary.md"
MODEL_PATH = ROOT / "models" / "v86" / "v86_model_registry_trust_center_model.json"


def U(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


MODEL_ROWS: List[Dict[str, Any]] = [
    {
        "code": "v41",
        "model_name_bg": U(r"Rules-aware \u0430\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u043e\u0441\u043d\u043e\u0432\u043d\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430"),
        "model_name_en": "Rules-aware Main Number Analysis",
        "category_bg": U(r"\u0411\u0430\u0437\u043e\u0432 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b"),
        "mode_bg": U(r"\u0421\u0438\u043d\u0445\u0440\u043e\u043d"),
        "lifecycle_bg": U(r"\u0421\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0438\u0440\u0430\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u0441\u0438\u043d\u0445\u0440\u043e\u043d"),
        "role_bg": U(r"\u0427\u0435\u0441\u0442\u043e\u0442\u0430, recency \u0438 SGD \u0441\u0438\u0433\u043d\u0430\u043b\u0438 \u0432\u044a\u0440\u0445\u0443 \u043f\u0440\u0430\u0432\u0438\u043b\u043d\u0438\u044f 6/49 \u043d\u0430\u0431\u043e\u0440 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438."),
        "status_note_bg": U(r"\u0411\u0430\u0437\u043e\u0432 \u0441\u0438\u0433\u043d\u0430\u043b\u0435\u043d \u0441\u043b\u043e\u0439."),
        "status_type": "synced",
        "artifacts": ["reports/v41_model_retraining_summary.json", "models/v41/v41_latest_predictions.json"],
        "primary_artifact": "reports/v41_model_retraining_summary.json"
    },
    {
        "code": "v50",
        "model_name_bg": U(r"\u0410\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u0434\u0432\u043e\u0439\u043a\u0438 \u0438 \u0433\u0440\u0443\u043f\u0438"),
        "model_name_en": "Pair and Group Intelligence",
        "category_bg": U(r"\u0421\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u0435\u043d \u0430\u043d\u0430\u043b\u0438\u0437"),
        "mode_bg": U(r"\u041e\u0442\u0447\u0435\u0442"),
        "lifecycle_bg": U(r"\u041f\u043e\u043c\u043e\u0449\u0435\u043d \u043e\u0442\u0447\u0435\u0442"),
        "health_status_bg": U(r"OK - \u043d\u0430\u043b\u0438\u0447\u0435\u043d"),
        "role_bg": U(r"\u041f\u043e\u043c\u0430\u0433\u0430 \u0441 \u0434\u0432\u043e\u0439\u043a\u0438 \u0438 \u0442\u0440\u043e\u0439\u043a\u0438 \u0447\u0438\u0441\u043b\u0430."),
        "status_note_bg": U(r"\u041f\u043e\u043c\u043e\u0449\u0435\u043d \u043e\u0442\u0447\u0435\u0442, \u043d\u0435 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430."),
        "status_type": "report",
        "artifacts": ["reports/v50_pair_group_summary.md", "scripts/v50_build_pair_group_intelligence.py"],
        "primary_artifact": "reports/v50_pair_group_summary.md"
    },
    {
        "code": "v51",
        "model_name_bg": U(r"\u041e\u0446\u0435\u043d\u043a\u0430 \u043d\u0430 \u043f\u0430\u043a\u0435\u0442 \u043e\u0442 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438"),
        "model_name_en": "Ticket Portfolio Intelligence",
        "category_bg": U(r"\u041f\u0430\u043a\u0435\u0442\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430"),
        "mode_bg": U(r"\u041e\u0442\u0447\u0435\u0442"),
        "lifecycle_bg": U(r"\u041f\u043e\u043c\u043e\u0449\u0435\u043d \u043e\u0442\u0447\u0435\u0442"),
        "health_status_bg": U(r"OK - \u043d\u0430\u043b\u0438\u0447\u0435\u043d"),
        "role_bg": U(r"\u041e\u0446\u0435\u043d\u044f\u0432\u0430 \u0444\u0438\u0448 \u043a\u0430\u0442\u043e \u043f\u0430\u043a\u0435\u0442, \u043d\u0435 \u0441\u0430\u043c\u043e \u0435\u0434\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f."),
        "status_note_bg": U(r"\u041f\u043e\u043c\u043e\u0449\u0435\u043d \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0444\u0438\u0448."),
        "status_type": "report",
        "artifacts": ["reports/v51_ticket_portfolio_summary.md", "scripts/v51_build_ticket_portfolio_intelligence.py"],
        "primary_artifact": "reports/v51_ticket_portfolio_summary.md"
    },
    {
        "code": "v58",
        "model_name_bg": U(r"\u041e\u0431\u0435\u0434\u0438\u043d\u0435\u043d\u0430 \u0443\u043c\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430"),
        "model_name_en": "Smart Ensemble Score",
        "category_bg": U(r"\u041e\u0431\u0435\u0434\u0438\u043d\u0435\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430"),
        "mode_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d"),
        "lifecycle_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u0430\u043a\u0442\u0438\u0432\u0435\u043d"),
        "role_bg": U(r"\u041e\u0431\u0435\u0434\u0438\u043d\u044f\u0432\u0430 \u043d\u044f\u043a\u043e\u043b\u043a\u043e \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0430."),
        "status_note_bg": U(r"\u0423\u0447\u0430\u0441\u0442\u0432\u0430 \u0432 \u043e\u0431\u0449\u0430\u0442\u0430 \u043e\u0446\u0435\u043d\u043a\u0430."),
        "status_type": "active",
        "artifacts": ["reports/v58_smart_ensemble_summary.json", "models/v58/v58_smart_ensemble_manifest.json"],
        "primary_artifact": "reports/v58_smart_ensemble_summary.json"
    },
    {
        "code": "v63",
        "model_name_bg": U(r"\u0422\u0430\u0431\u043b\u043e \u0437\u0430 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
        "model_name_en": "Model Reliability Dashboard",
        "category_bg": U(r"\u041a\u043e\u043d\u0442\u0440\u043e\u043b \u043d\u0430 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442"),
        "mode_bg": U(r"\u041a\u043e\u043d\u0442\u0440\u043e\u043b"),
        "lifecycle_bg": U(r"\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u0435\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u043a\u043e\u043d\u0442\u0440\u043e\u043b"),
        "role_bg": U(r"\u041f\u043e\u043a\u0430\u0437\u0432\u0430 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442."),
        "status_note_bg": U(r"\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u0435\u043d \u0441\u043b\u043e\u0439 \u0437\u0430 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442."),
        "status_type": "control",
        "artifacts": ["reports/v63_model_reliability_summary.json", "reports/v63_model_reliability_scores.csv"],
        "primary_artifact": "reports/v63_model_reliability_summary.json"
    },
    {
        "code": "v65",
        "model_name_bg": U(r"\u0410\u0434\u0430\u043f\u0442\u0438\u0432\u043d\u043e \u0442\u0435\u0433\u043b\u043e \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
        "model_name_en": "Adaptive Model Weighting",
        "category_bg": U(r"\u0410\u0434\u0430\u043f\u0442\u0438\u0432\u043d\u0438 \u0442\u0435\u0433\u043b\u0430"),
        "mode_bg": U(r"\u0421\u0438\u043d\u0445\u0440\u043e\u043d"),
        "lifecycle_bg": U(r"\u0421\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0438\u0440\u0430\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u0441\u0438\u043d\u0445\u0440\u043e\u043d"),
        "role_bg": U(r"\u041f\u0440\u0435\u0432\u0440\u044a\u0449\u0430 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442\u0442\u0430 \u0432 \u0442\u0435\u0433\u043b\u0430."),
        "status_note_bg": U(r"\u0423\u043f\u0440\u0430\u0432\u043b\u044f\u0432\u0430 \u0442\u0435\u0433\u043b\u0430\u0442\u0430 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435."),
        "status_type": "synced",
        "artifacts": ["reports/v65_model_weighting_summary.json", "reports/v65_model_weights.csv", "models/v65/v65_model_weighting_center_model.json"],
        "primary_artifact": "reports/v65_model_weighting_summary.json"
    },
    {
        "code": "v66",
        "model_name_bg": U(r"\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d \u043e\u0431\u0435\u0434\u0438\u043d\u0435\u043d \u043c\u043e\u0434\u0435\u043b"),
        "model_name_en": "Weighted Smart Ensemble",
        "category_bg": U(r"\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d \u043e\u0431\u0435\u0434\u0438\u043d\u0435\u043d \u0430\u043d\u0430\u043b\u0438\u0437"),
        "mode_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d"),
        "lifecycle_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u0430\u043a\u0442\u0438\u0432\u0435\u043d"),
        "role_bg": U(r"\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430 \u0441\u0438\u0433\u043d\u0430\u043b\u0438\u0442\u0435 \u0441 \u0442\u0435\u0433\u043b\u0430."),
        "status_note_bg": U(r"\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d \u0430\u043a\u0442\u0438\u0432\u0435\u043d scoring \u0441\u043b\u043e\u0439."),
        "status_type": "active",
        "artifacts": ["reports/v66_weighted_smart_ensemble_summary.json", "models/v66/v66_weighted_smart_ensemble_model.json"],
        "primary_artifact": "reports/v66_weighted_smart_ensemble_summary.json"
    },
    {
        "code": "v70",
        "model_name_bg": U(r"\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043f\u0430\u043a\u0435\u0442"),
        "model_name_en": "Applied Candidate Portfolio",
        "category_bg": U(r"\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d \u0440\u0435\u0444\u0435\u0440\u0435\u043d\u0442\u0435\u043d \u043f\u0430\u043a\u0435\u0442"),
        "mode_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d"),
        "lifecycle_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u0430\u043a\u0442\u0438\u0432\u0435\u043d"),
        "role_bg": U(r"\u041f\u0430\u0437\u0438 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d \u0440\u0435\u0444\u0435\u0440\u0435\u043d\u0442\u0435\u043d \u043f\u0430\u043a\u0435\u0442."),
        "status_note_bg": U(r"\u0420\u0435\u0444\u0435\u0440\u0435\u043d\u0442\u0435\u043d \u043f\u0430\u043a\u0435\u0442 \u0437\u0430 \u043e\u0446\u0435\u043d\u043a\u0430."),
        "status_type": "active",
        "artifacts": ["reports/v70_applied_candidate_portfolio_summary.json", "models/v70/v70_applied_candidate_portfolio_model.json"],
        "primary_artifact": "reports/v70_applied_candidate_portfolio_summary.json"
    },
    {
        "code": "v75",
        "model_name_bg": U(r"\u041d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u043c\u0435\u0442\u0430 \u043c\u043e\u0434\u0435\u043b"),
        "model_name_en": "Neural Meta Learner",
        "category_bg": U(r"\u041d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u043c\u0435\u0442\u0430 \u0441\u043b\u043e\u0439"),
        "mode_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d"),
        "lifecycle_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u0430\u043a\u0442\u0438\u0432\u0435\u043d"),
        "role_bg": U(r"\u0410\u043a\u0442\u0438\u0432\u0435\u043d \u043d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u0441\u043b\u043e\u0439 \u0441 90 epochs."),
        "status_note_bg": U(r"\u0422\u0435\u043a\u0443\u0449\u0438\u044f\u0442 \u0430\u043a\u0442\u0438\u0432\u0435\u043d \u043d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u0438\u0437\u0431\u043e\u0440."),
        "status_type": "active",
        "artifacts": ["reports/v75_neural_meta_learner_summary.json", "models/v75/v75_neural_meta_learner_model.json"],
        "primary_artifact": "reports/v75_neural_meta_learner_summary.json"
    },
    {
        "code": "v84",
        "model_name_bg": U(r"\u0421\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438 \u0432\u044a\u0432 \u0432\u0440\u0435\u043c\u0435\u0442\u043e"),
        "model_name_en": "Model Comparison Forward Test",
        "category_bg": U(r"\u0417\u0430\u043a\u043b\u044e\u0447\u0435\u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "mode_bg": U(r"\u041a\u043e\u043d\u0442\u0440\u043e\u043b"),
        "lifecycle_bg": U(r"\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u0435\u043d \u0441\u043b\u043e\u0439"),
        "health_status_bg": U(r"OK - \u043a\u043e\u043d\u0442\u0440\u043e\u043b"),
        "role_bg": U(r"\u0417\u0430\u043a\u043b\u044e\u0447\u0432\u0430 48 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0437\u0430 \u0431\u044a\u0434\u0435\u0449\u0430 \u0440\u0435\u0430\u043b\u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430."),
        "status_note_bg": U(r"48 \u0440\u0435\u0434\u0430, 1 snapshot, 6 \u0433\u0440\u0443\u043f\u0438 x 8 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438."),
        "status_type": "control",
        "artifacts": ["reports/v84_model_comparison_summary.json", "data/v84_model_forward_test_snapshots.csv", "models/v84/v84_model_comparison_forward_test_model.json"],
        "primary_artifact": "reports/v84_model_comparison_summary.json"
    },
    {
        "code": "v85",
        "model_name_bg": U(r"\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u043d\u0435\u0432\u0440\u043e\u043d\u043d\u0438 \u0435\u043f\u043e\u0445\u0438"),
        "model_name_en": "Neural Epoch Comparison Audit",
        "category_bg": U(r"\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "mode_bg": U(r"\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "lifecycle_bg": U(r"\u0421\u0430\u043c\u043e \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "health_status_bg": U(r"OK - \u0441\u0430\u043c\u043e \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "role_bg": U(r"\u0421\u0440\u0430\u0432\u043d\u044f\u0432\u0430 90, 150, 300 \u0438 500 epochs. \u041d\u0435 \u0441\u043c\u0435\u043d\u044f \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u044f \u043c\u043e\u0434\u0435\u043b."),
        "status_note_bg": U(r"\u041d\u0430\u0439-\u0434\u043e\u0431\u044a\u0440 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442: 90 epochs. 500 \u043d\u0435 \u0435 \u0430\u043a\u0442\u0438\u0432\u0435\u043d."),
        "status_type": "audit",
        "artifacts": ["reports/v85_neural_epoch_comparison_summary.json", "reports/v85_neural_epoch_comparison.csv", "models/v85/v85_neural_epoch_comparison_model.json"],
        "primary_artifact": "reports/v85_neural_epoch_comparison_summary.json"
    }
]


def _read_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _dataset_overview() -> Dict[str, Any]:
    rows = _read_rows(DATASET_PATH)
    source = DATASET_PATH
    if not rows:
        rows = _read_rows(FALLBACK_DATASET_PATH)
        source = FALLBACK_DATASET_PATH

    latest = rows[-1] if rows else {}
    numbers = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = str(latest.get(key, "")).strip()
        if value:
            numbers.append(value)

    return {
        "dataset_source": source.relative_to(ROOT).as_posix(),
        "dataset_rows": len(rows),
        "latest_draw_date": latest.get("date", ""),
        "latest_draw_index": latest.get("source_draw_id") or latest.get("draw_id") or len(rows),
        "latest_numbers": ",".join(numbers)
    }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return default


def _artifact_status(paths: List[str]) -> Dict[str, Any]:
    missing = [path for path in paths if not (ROOT / path).exists()]
    return {
        "artifacts_expected": len(paths),
        "artifacts_present": len(paths) - len(missing),
        "missing_artifacts": "; ".join(missing)
    }


def _draw_reference(row: Dict[str, Any], dataset: Dict[str, Any]) -> str:
    if row["code"] == "v85":
        return "90/150/300/500"
    if row["code"] == "v84":
        return "48"
    return str(dataset["dataset_rows"])


def _build_rows(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for item in MODEL_ROWS:
        status = _artifact_status(item["artifacts"])
        row = dict(item)
        row.update(status)
        row["draw_reference"] = _draw_reference(item, dataset)
        row["dataset_rows"] = dataset["dataset_rows"]
        row.pop("artifacts", None)
        rows.append(row)
    return rows


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = [
        "code",
        "model_name_bg",
        "model_name_en",
        "category_bg",
        "mode_bg",
        "lifecycle_bg",
        "health_status_bg",
        "draw_reference",
        "dataset_rows",
        "artifacts_present",
        "artifacts_expected",
        "primary_artifact",
        "missing_artifacts",
        "role_bg",
        "status_note_bg",
        "status_type"
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_markdown(path: Path, summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    lines = [
        "# " + U(r"\u0420\u0435\u0433\u0438\u0441\u0442\u044a\u0440 \u0438 \u0434\u043e\u0432\u0435\u0440\u0438\u0435 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
        "",
        U(r"\u0420\u0435\u0434\u043e\u0432\u0435 \u0432 \u043d\u0430\u0431\u043e\u0440\u0430 \u0434\u0430\u043d\u043d\u0438") + f": **{summary['dataset_rows']}**",
        U(r"\u041f\u043e\u0441\u043b\u0435\u0434\u0435\u043d \u0442\u0438\u0440\u0430\u0436") + f": **{summary['latest_draw_date']}** - {summary['latest_numbers']}",
        "",
        U(r"\u0422\u043e\u0437\u0438 \u043e\u0442\u0447\u0435\u0442 \u043e\u0431\u044f\u0441\u043d\u044f\u0432\u0430 \u043a\u043e\u0439 \u043c\u043e\u0434\u0435\u043b \u043a\u0430\u043a\u0432\u0430 \u0440\u043e\u043b\u044f \u0438\u043c\u0430. \u041d\u0435 \u0435 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430 \u0438 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f."),
        "",
        "| " + U(r"\u041a\u043e\u0434") + " | " + U(r"\u0418\u043c\u0435") + " | " + U(r"\u0421\u0442\u0430\u0442\u0443\u0441") + " | " + U(r"\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430") + " |",
        "|---|---|---|---|"
    ]
    for row in rows:
        lines.append(f"| {row['code']} | {row['model_name_bg']} | {row['lifecycle_bg']} | {row['health_status_bg']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_model_registry_trust_center() -> Dict[str, Any]:
    dataset = _dataset_overview()
    rows = _build_rows(dataset)
    missing_rows = [row for row in rows if row["missing_artifacts"]]
    active_rows = [row for row in rows if row["status_type"] == "active"]
    audit_rows = [row for row in rows if row["status_type"] == "audit"]
    control_rows = [row for row in rows if row["status_type"] == "control"]

    summary = {
        "step": 86,
        "name": "Model Registry & Trust Center",
        "status": "OK" if not missing_rows else "CHECK_MISSING_ARTIFACTS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_source": dataset["dataset_source"],
        "dataset_rows": dataset["dataset_rows"],
        "latest_draw_date": dataset["latest_draw_date"],
        "latest_draw_index": dataset["latest_draw_index"],
        "latest_numbers": dataset["latest_numbers"],
        "models_registered": len(rows),
        "active_models": len(active_rows),
        "audit_only_models": len(audit_rows),
        "control_models": len(control_rows),
        "missing_models": len(missing_rows),
        "active_model_names": [row["model_name_bg"] for row in active_rows],
        "audit_only_model_names": [row["model_name_bg"] for row in audit_rows],
        "safe_note": U(r"\u0422\u043e\u0432\u0430 \u0435 \u0440\u0435\u0433\u0438\u0441\u0442\u044a\u0440 \u0438 \u043a\u043e\u043d\u0442\u0440\u043e\u043b \u043d\u0430 \u0434\u043e\u0432\u0435\u0440\u0438\u0435 \u043c\u0435\u0436\u0434\u0443 \u043c\u043e\u0434\u0435\u043b\u0438. \u041d\u0435 \u0435 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430 \u0438 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.")
    }

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(CSV_PATH, rows)
    _write_markdown(MD_PATH, summary, rows)
    MODEL_PATH.write_text(json.dumps({"summary": summary, "models": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"summary": summary, "models": rows}


if __name__ == "__main__":
    result = build_model_registry_trust_center()
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
