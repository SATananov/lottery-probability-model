from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
import json
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
HISTORICAL_DATASET_PATH = ROOT / "data" / "historical_draws.csv"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"

SUMMARY_PATH = REPORTS_DIR / "v86_model_registry_summary.json"
REGISTRY_CSV_PATH = REPORTS_DIR / "v86_model_registry_models.csv"
SUMMARY_MD_PATH = REPORTS_DIR / "v86_model_registry_summary.md"
MODEL_PATH = MODELS_DIR / "v86" / "v86_model_registry_trust_center_model.json"

REGISTRY_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "code": "v41",
        "name_bg": "Rules-aware ?????? ?? ????????? ?????",
        "name_en": "Rules-aware Main Number Analysis",
        "category_bg": "??????? ????????????? ?????",
        "role_bg": "??????? ????????, recency ? SGD ??????? ????? ????????? 6/49 dataset.",
        "lifecycle_bg": "????????????? ???????? ?????",
        "mode_bg": "???????? ????????",
        "artifact_paths": [
            "reports/v41_model_retraining_summary.json",
            "models/v41/v41_latest_predictions.json"
        ],
        "summary_path": "reports/v41_model_retraining_summary.json",
        "draw_field": "total_draw_events",
        "status_note_bg": "???? ???? ? ???????? ?? ???????? ??????? 6/49 ??????? ??? bonus ?????."
    },
    {
        "code": "v50",
        "name_bg": "Pair and Group Intelligence",
        "name_en": "Pair and Group Intelligence",
        "category_bg": "??????????? ?????????? ??????",
        "role_bg": "????? ?????? ? ?????? ?????, ????? ?? ????? ?? ??????????? ?? ????????????.",
        "lifecycle_bg": "Report-only ??????? ????",
        "mode_bg": "??????? ??????",
        "artifact_paths": [
            "reports/v50_pair_group_summary.md",
            "scripts/v50_build_pair_group_intelligence.py"
        ],
        "summary_path": "reports/v50_pair_group_summary.md",
        "draw_field": "",
        "status_note_bg": "?? ? ????????????? ????????, ? ?????????? ?????? ?? ????? ??????."
    },
    {
        "code": "v51",
        "name_bg": "Ticket Portfolio Intelligence",
        "name_en": "Ticket Portfolio Intelligence",
        "category_bg": "??????? ??????",
        "role_bg": "??????? ????? ?? ??????????, ?????????? ? ???????????? ????? ????????.",
        "lifecycle_bg": "Report-only ??????? ????",
        "mode_bg": "??????? ??????",
        "artifact_paths": [
            "reports/v51_ticket_portfolio_summary.md",
            "scripts/v51_build_ticket_portfolio_intelligence.py"
        ],
        "summary_path": "reports/v51_ticket_portfolio_summary.md",
        "draw_field": "",
        "status_note_bg": "?????? ?? ?? ??????? ???? ???? ??????????, ? ????? ?????."
    },
    {
        "code": "v58",
        "name_bg": "Smart Ensemble Score",
        "name_en": "Smart Ensemble Score",
        "category_bg": "????????? ??????",
        "role_bg": "????????? ???????? ????????????? ??????? ? ???? ?????? ?? ????? ? ??????????.",
        "lifecycle_bg": "??????? scoring ????",
        "mode_bg": "??????? ??????? ?????",
        "artifact_paths": [
            "reports/v58_smart_ensemble_summary.json",
            "models/v58/v58_smart_ensemble_manifest.json"
        ],
        "summary_path": "reports/v58_smart_ensemble_summary.json",
        "draw_field": "valid_draws",
        "status_note_bg": "???????? ?? ???? ???? ?? ????????????? ??????, ?? ?? ? ???????? ?? ????????."
    },
    {
        "code": "v63",
        "name_bg": "Model Reliability Dashboard",
        "name_en": "Model Reliability Dashboard",
        "category_bg": "??????? ?? ??????????",
        "role_bg": "??????? ????????????? post-draw ??????????? ?? ????????.",
        "lifecycle_bg": "????????? ????",
        "mode_bg": "???????",
        "artifact_paths": [
            "reports/v63_model_reliability_summary.json",
            "reports/v63_model_reliability_scores.csv"
        ],
        "summary_path": "reports/v63_model_reliability_summary.json",
        "draw_field": "",
        "status_note_bg": "??????? ??? ?????? ?? ?? ??????? ??-???????? ???????????."
    },
    {
        "code": "v65",
        "name_bg": "Adaptive Model Weighting",
        "name_en": "Adaptive Model Weighting",
        "category_bg": "????????? ?????",
        "role_bg": "???????? ???????????? ?? Step 63 ? ????? ?? ????????.",
        "lifecycle_bg": "????????????? ??????? ????",
        "mode_bg": "?????????????",
        "artifact_paths": [
            "reports/v65_model_weighting_summary.json",
            "reports/v65_model_weights.csv",
            "models/v65/v65_model_weighting_center_model.json"
        ],
        "summary_path": "reports/v65_model_weighting_summary.json",
        "draw_field": "",
        "status_note_bg": "???? ? ???? ?? ?????????? ?? ??????? ? ??????, ?? ????????????? ????????."
    },
    {
        "code": "v66",
        "name_bg": "Weighted Smart Ensemble",
        "name_en": "Weighted Smart Ensemble",
        "category_bg": "????????? ???????? ??????",
        "role_bg": "????????? ????????? ? ??????????? ????? ?? Step 65.",
        "lifecycle_bg": "??????? scoring ????",
        "mode_bg": "??????? ??????? ?????",
        "artifact_paths": [
            "reports/v66_weighted_smart_ensemble_summary.json",
            "models/v66/v66_weighted_smart_ensemble_model.json"
        ],
        "summary_path": "reports/v66_weighted_smart_ensemble_summary.json",
        "draw_field": "valid_draws",
        "status_note_bg": "???? ? ???? ?? ????????? scoring ?????? ???? ????????? ?? ?????."
    },
    {
        "code": "v70",
        "name_bg": "Applied Candidate Portfolio",
        "name_en": "Applied Candidate Portfolio",
        "category_bg": "???????? ?????????? ?????",
        "role_bg": "???? ???????? ???????? ????? ?? ????????? ? ?????????? ??????.",
        "lifecycle_bg": "??????? ?????????? ?????",
        "mode_bg": "??????? ?????????? ????",
        "artifact_paths": [
            "reports/v70_applied_candidate_portfolio_summary.json",
            "models/v70/v70_applied_candidate_portfolio_model.json"
        ],
        "summary_path": "reports/v70_applied_candidate_portfolio_summary.json",
        "draw_field": "valid_draws",
        "status_note_bg": "?? ?????? ????????????, ? ???? ???????????? ?????????? ?????? ?? ??????."
    },
    {
        "code": "v75",
        "name_bg": "Neural Meta Learner",
        "name_en": "Neural Meta Learner",
        "category_bg": "???????? ???? ????",
        "role_bg": "?????? neural meta-layer ????? 10058 ?????? ? 90 epochs.",
        "lifecycle_bg": "??????? ???????? ?????",
        "mode_bg": "??????? ?????",
        "artifact_paths": [
            "reports/v75_neural_meta_learner_summary.json",
            "models/v75/v75_neural_meta_learner_model.json"
        ],
        "summary_path": "reports/v75_neural_meta_learner_summary.json",
        "draw_field": "valid_draws",
        "status_note_bg": "???????? ??????? neural ????? ? 90 epochs, ?????? Step 85 ?? ?????? ??-????? 500 epochs ???????."
    },
    {
        "code": "v84",
        "name_bg": "Model Comparison Forward Test",
        "name_en": "Model Comparison Forward Test",
        "category_bg": "????????? ???????? ??? ???????",
        "role_bg": "???? ???????? snapshot ?? 48 ?????????? ?? ?????? ???????? ???? ????? ?????.",
        "lifecycle_bg": "????????? snapshot ????",
        "mode_bg": "???????",
        "artifact_paths": [
            "reports/v84_model_comparison_summary.json",
            "data/v84_model_forward_test_snapshots.csv",
            "models/v84/v84_model_comparison_forward_test_model.json"
        ],
        "summary_path": "reports/v84_model_comparison_summary.json",
        "draw_field": "latest_draw_index",
        "status_note_bg": "??????? 48 ????????? ??????????, 1 snapshot, 6 ????? ?? 8 ??????????."
    },
    {
        "code": "v85",
        "name_bg": "Neural Epoch Comparison Audit",
        "name_en": "Neural Epoch Comparison Audit",
        "category_bg": "???????? audit",
        "role_bg": "???????? 90, 150, 300 ? 500 epochs, ??? ?? ????? ???????? ?????.",
        "lifecycle_bg": "Audit-only",
        "mode_bg": "Audit-only",
        "artifact_paths": [
            "reports/v85_neural_epoch_comparison_summary.json",
            "reports/v85_neural_epoch_comparison.csv",
            "models/v85/v85_neural_epoch_comparison_model.json"
        ],
        "summary_path": "reports/v85_neural_epoch_comparison_summary.json",
        "draw_field": "valid_draws",
        "status_note_bg": "Best=90 epochs. 500 epochs ?? ? ??????? ?????."
    }
]


def _load_json(rel_path: str) -> Optional[Dict[str, Any]]:
    path = ROOT / rel_path
    if not path.exists() or path.suffix.lower() != ".json":
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _dataset_overview() -> Dict[str, Any]:
    rows = _read_csv_rows(DATASET_PATH)
    source = DATASET_PATH.relative_to(ROOT).as_posix()
    if not rows:
        rows = _read_csv_rows(HISTORICAL_DATASET_PATH)
        source = HISTORICAL_DATASET_PATH.relative_to(ROOT).as_posix()

    latest = rows[-1] if rows else {}
    numbers = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = str(latest.get(key, "")).strip()
        if value:
            numbers.append(value)

    return {
        "dataset_source": source,
        "dataset_rows": len(rows),
        "latest_draw_date": latest.get("date", ""),
        "latest_draw_index": latest.get("source_draw_id") or latest.get("draw_id") or latest.get("draw_event_id") or len(rows),
        "latest_numbers": ",".join(numbers)
    }


def _artifact_status(paths: List[str]) -> Dict[str, Any]:
    missing = [p for p in paths if not (ROOT / p).exists()]
    return {
        "artifacts_expected": len(paths),
        "artifacts_present": len(paths) - len(missing),
        "missing_artifacts": missing,
        "artifacts_ok": len(missing) == 0
    }


def _extract_draw_reference(definition: Dict[str, Any], summary: Optional[Dict[str, Any]]) -> str:
    if not summary:
        return ""
    field = str(definition.get("draw_field", "") or "")
    if field and field in summary:
        return str(summary.get(field, ""))
    for fallback in ["valid_draws", "total_draw_events", "latest_draw_index", "dataset_rows"]:
        if fallback in summary:
            return str(summary.get(fallback, ""))
    return ""


def _registry_row(definition: Dict[str, Any], dataset: Dict[str, Any], sync_summary: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    artifacts = _artifact_status(list(definition.get("artifact_paths", [])))
    summary = _load_json(str(definition.get("summary_path", "")))
    draw_reference = _extract_draw_reference(definition, summary)
    code = definition["code"]

    if not artifacts["artifacts_ok"]:
        health = "?????? ????????"
    elif code == "v85":
        best = _safe_int((summary or {}).get("best_epochs_by_test_avg_hits"), default=0)
        health = "OK - audit-only, best=90" if best == 90 else "??????? audit ?????????"
    elif code == "v84":
        locked = _safe_int((summary or {}).get("locked_snapshot_records"), default=0)
        rows = _safe_int((summary or {}).get("snapshot_rows_recorded"), default=0)
        health = "OK - ???????? snapshot" if locked == 1 and rows == 48 else "??????? snapshot"
    elif sync_summary and sync_summary.get("all_synced") is True:
        health = "OK - ?????????????"
    else:
        health = "OK - ???????"

    return {
        "code": code,
        "model_name_bg": definition.get("name_bg", ""),
        "model_name_en": definition.get("name_en", ""),
        "category_bg": definition.get("category_bg", ""),
        "role_bg": definition.get("role_bg", ""),
        "mode_bg": definition.get("mode_bg", ""),
        "lifecycle_bg": definition.get("lifecycle_bg", ""),
        "health_status_bg": health,
        "draw_reference": draw_reference,
        "dataset_rows": dataset.get("dataset_rows", 0),
        "artifacts_present": artifacts["artifacts_present"],
        "artifacts_expected": artifacts["artifacts_expected"],
        "missing_artifacts": "; ".join(artifacts["missing_artifacts"]),
        "primary_artifact": definition.get("summary_path", ""),
        "status_note_bg": definition.get("status_note_bg", "")
    }


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
        "status_note_bg"
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _write_markdown(path: Path, summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    lines = [
        "# Step 86 - Model Registry & Trust Center",
        "",
        f"Dataset rows: **{summary.get('dataset_rows')}**",
        f"Last draw: **{summary.get('latest_draw_date')}** - {summary.get('latest_numbers')}",
        f"Registered models: **{summary.get('models_registered')}**",
        f"Active models/layers: **{summary.get('active_models')}**",
        f"Audit-only models: **{summary.get('audit_only_models')}**",
        "",
        "This page is a registry and trust-control layer. It is not a winning guarantee.",
        "",
        "| Code | Human name | Status | Health |",
        "|---|---|---|---|"
    ]
    for row in rows:
        lines.append(
            f"| {row.get('code')} | {row.get('model_name_en')} | {row.get('lifecycle_bg')} | {row.get('health_status_bg')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_model_registry_trust_center() -> Dict[str, Any]:
    dataset = _dataset_overview()
    sync_summary = _load_json("reports/v74_model_dependency_summary.json")
    rows = [_registry_row(definition, dataset, sync_summary) for definition in REGISTRY_DEFINITIONS]

    active_models = [row for row in rows if "???????" in row.get("lifecycle_bg", "")]
    audit_only = [row for row in rows if "Audit-only" in row.get("lifecycle_bg", "")]
    control_models = [row for row in rows if "???????" in row.get("mode_bg", "") or "???????" in row.get("lifecycle_bg", "")]
    missing_models = [row for row in rows if row.get("missing_artifacts")]

    summary = {
        "step": 86,
        "name": "Model Registry & Trust Center",
        "status": "OK" if not missing_models else "CHECK_MISSING_ARTIFACTS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_source": dataset.get("dataset_source"),
        "dataset_rows": dataset.get("dataset_rows"),
        "latest_draw_date": dataset.get("latest_draw_date"),
        "latest_draw_index": dataset.get("latest_draw_index"),
        "latest_numbers": dataset.get("latest_numbers"),
        "models_registered": len(rows),
        "active_models": len(active_models),
        "audit_only_models": len(audit_only),
        "control_models": len(control_models),
        "missing_models": len(missing_models),
        "active_model_names": [row["model_name_bg"] for row in active_models],
        "audit_only_model_names": [row["model_name_bg"] for row in audit_only],
        "safe_note": "???? ? ???????? ? ??????? ?? ??????? ????? ??????. ?? ? ???????? ? ?? ? ???????? ?? ???????.",
        "generated_reports": [
            SUMMARY_PATH.relative_to(ROOT).as_posix(),
            REGISTRY_CSV_PATH.relative_to(ROOT).as_posix(),
            SUMMARY_MD_PATH.relative_to(ROOT).as_posix(),
            MODEL_PATH.relative_to(ROOT).as_posix()
        ]
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(REGISTRY_CSV_PATH, rows)
    _write_markdown(SUMMARY_MD_PATH, summary, rows)
    MODEL_PATH.write_text(
        json.dumps({"summary": summary, "models": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    return {"summary": summary, "models": rows}


if __name__ == "__main__":
    result = build_model_registry_trust_center()
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
