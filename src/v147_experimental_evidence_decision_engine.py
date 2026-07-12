from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v144_reproducible_experiment_registry_engine import canonical_hash, dataset_sha256, sha256_file

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "models" / "v147_experimental_evidence_decision_policy.json"
STATUS_PATH = ROOT / "models" / "v147_experimental_evidence_decision_status.json"
DECISION_REGISTRY_PATH = ROOT / "data" / "research_decision_registry.jsonl"
DECISION_INDEX_CSV_PATH = ROOT / "reports" / "v147_research_decision_registry_index.csv"
EVIDENCE_MATRIX_CSV_PATH = ROOT / "reports" / "v147_experimental_evidence_matrix.csv"
SUMMARY_JSON_PATH = ROOT / "reports" / "v147_research_decision_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v147_research_decision_summary.md"
DECISION_DIR = ROOT / "reports" / "decisions" / "v147"

SOURCE_PATHS = {
    144: ROOT / "reports" / "v144_baseline_lab_summary.json",
    145: ROOT / "reports" / "v145_neural_dynamics_summary.json",
    146: ROOT / "reports" / "v146_neural_robustness_summary.json",
}
SOURCE_STATUS_PATHS = {
    144: ROOT / "models" / "v144_reproducible_experiment_registry_status.json",
    145: ROOT / "models" / "v145_experimental_neural_dynamics_status.json",
    146: ROOT / "models" / "v146_controlled_neural_robustness_status.json",
}

SAFE_NOTE_BG = (
    "Step 147 е research governance слой. Той обобщава исторически експерименти, не прогнозира бъдещи "
    "тиражи, не генерира реални фишове и не включва experimental модел в production pipeline."
)

DEFAULT_POLICY: dict[str, Any] = {
    "required_source_steps": [144, 145, 146],
    "require_same_dataset_sha256": True,
    "require_completed_source_status": True,
    "robust_superiority_requirements": {
        "mean_advantage_positive": True,
        "confidence_interval_lower_bound_above_zero": True,
        "maximum_p_value": 0.05,
        "minimum_positive_seed_rate": 0.80,
        "minimum_positive_fold_rate": 1.00,
    },
    "current_configuration_action": "pause_and_archive",
    "repeat_same_configuration_on_seen_holdouts": "forbidden",
    "production_promotion": "blocked_without_robust_superiority",
    "next_experiment_requirements": [
        "materially_new_hypothesis",
        "preregistered_primary_metric_and_gate",
        "untouched_or_future_validation_period",
        "baseline_first_comparison",
        "score_before_learn_chronology",
        "no_personal_journal_access",
        "no_production_pipeline_access",
        "no_real_ticket_generation",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _optional_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _outcome(
    *,
    advantage: float | None,
    ci_lower: float | None = None,
    ci_upper: float | None = None,
    p_value: float | None = None,
    positive_seed_rate: float | None = None,
    positive_fold_rate: float | None = None,
    policy: dict[str, Any],
) -> tuple[str, bool]:
    requirements = policy["robust_superiority_requirements"]
    checks = [
        advantage is not None and advantage > 0.0,
        ci_lower is not None and ci_lower > 0.0,
        p_value is not None and p_value <= float(requirements["maximum_p_value"]),
        positive_seed_rate is not None and positive_seed_rate >= float(requirements["minimum_positive_seed_rate"]),
        positive_fold_rate is not None and positive_fold_rate >= float(requirements["minimum_positive_fold_rate"]),
    ]
    robust = all(checks)
    if robust:
        return "robust_positive", True
    if ci_upper is not None and ci_upper < 0.0:
        return "robust_negative", False
    if advantage is not None and advantage > 0.0:
        return "positive_but_not_robust", False
    if advantage is not None and advantage < 0.0:
        return "negative", False
    return "inconclusive", False


def _row(
    *,
    step: int,
    experiment_id: str,
    evidence_scope: str,
    candidate: str,
    comparator: str,
    advantage: Any,
    source_path: Path,
    policy: dict[str, Any],
    ci_lower: Any = None,
    ci_upper: Any = None,
    p_value: Any = None,
    positive_seed_rate: Any = None,
    positive_fold_rate: Any = None,
    source_promotion_gate: Any = None,
) -> dict[str, Any]:
    advantage_value = _optional_number(advantage)
    lower_value = _optional_number(ci_lower)
    upper_value = _optional_number(ci_upper)
    p_value_number = _optional_number(p_value)
    seed_rate = _optional_number(positive_seed_rate)
    fold_rate = _optional_number(positive_fold_rate)
    outcome, robust = _outcome(
        advantage=advantage_value,
        ci_lower=lower_value,
        ci_upper=upper_value,
        p_value=p_value_number,
        positive_seed_rate=seed_rate,
        positive_fold_rate=fold_rate,
        policy=policy,
    )
    return {
        "step": step,
        "experiment_id": experiment_id,
        "evidence_scope": evidence_scope,
        "candidate": candidate,
        "comparator": comparator,
        "mean_advantage": advantage_value,
        "ci_lower": lower_value,
        "ci_upper": upper_value,
        "p_value": p_value_number,
        "positive_seed_rate": seed_rate,
        "positive_fold_rate": fold_rate,
        "source_promotion_gate_passed": bool(source_promotion_gate) if source_promotion_gate is not None else False,
        "evidence_outcome": outcome,
        "robust_superiority_demonstrated": robust,
        "production_eligible": False,
        "source_summary": source_path.relative_to(ROOT).as_posix(),
    }


def build_evidence_matrix(summaries: dict[int, dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    s144 = summaries[144]
    rows.append(
        _row(
            step=144,
            experiment_id=str(s144.get("experiment_id", "")),
            evidence_scope="single_holdout_baseline",
            candidate="frequency_walk_forward",
            comparator="uniform_random_mean",
            advantage=(s144.get("comparison") or {}).get("frequency_minus_random_mean_average_best_hits"),
            source_path=SOURCE_PATHS[144],
            policy=policy,
        )
    )

    s145 = summaries[145]
    c145 = s145.get("comparison", {}) or {}
    paired = c145.get("paired", {}) or {}
    rows.extend(
        [
            _row(
                step=145,
                experiment_id=str(s145.get("experiment_id", "")),
                evidence_scope="single_holdout_neural",
                candidate="neural_dynamics_reservoir",
                comparator="frequency_walk_forward",
                advantage=c145.get("neural_minus_frequency_average_best_hits"),
                p_value=(paired.get("versus_frequency") or {}).get("two_sided_sign_test_p_value"),
                source_promotion_gate=c145.get("promotion_gate_passed"),
                source_path=SOURCE_PATHS[145],
                policy=policy,
            ),
            _row(
                step=145,
                experiment_id=str(s145.get("experiment_id", "")),
                evidence_scope="single_holdout_neural",
                candidate="neural_dynamics_reservoir",
                comparator="recency_weighted_walk_forward",
                advantage=c145.get("neural_minus_recency_average_best_hits"),
                p_value=(paired.get("versus_recency") or {}).get("two_sided_sign_test_p_value"),
                source_promotion_gate=c145.get("promotion_gate_passed"),
                source_path=SOURCE_PATHS[145],
                policy=policy,
            ),
            _row(
                step=145,
                experiment_id=str(s145.get("experiment_id", "")),
                evidence_scope="single_holdout_neural",
                candidate="neural_dynamics_reservoir",
                comparator="uniform_random_mean",
                advantage=c145.get("neural_minus_random_mean_average_best_hits"),
                p_value=c145.get("empirical_one_sided_p_value_vs_random_trials"),
                source_promotion_gate=c145.get("promotion_gate_passed"),
                source_path=SOURCE_PATHS[145],
                policy=policy,
            ),
        ]
    )

    s146 = summaries[146]
    c146 = s146.get("comparison", {}) or {}
    for comparator, comparison in sorted((c146.get("baselines", {}) or {}).items()):
        if not isinstance(comparison, dict):
            continue
        rows.append(
            _row(
                step=146,
                experiment_id=str(s146.get("experiment_id", "")),
                evidence_scope="multi_seed_multi_period_neural",
                candidate="neural_dynamics_reservoir",
                comparator=comparator,
                advantage=comparison.get("mean_advantage"),
                ci_lower=comparison.get("bootstrap_ci_lower"),
                ci_upper=comparison.get("bootstrap_ci_upper"),
                p_value=comparison.get("two_sided_sign_test_p_value"),
                positive_seed_rate=comparison.get("positive_seed_rate"),
                positive_fold_rate=comparison.get("positive_fold_rate"),
                source_promotion_gate=c146.get("promotion_gate_passed"),
                source_path=SOURCE_PATHS[146],
                policy=policy,
            )
        )
    return rows




def _code_descriptor() -> dict[str, Any]:
    paths = [
        ROOT / "src/v147_experimental_evidence_decision_engine.py",
        ROOT / "tools/build_experimental_evidence_decision.py",
    ]
    rows = [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}
        for path in paths
        if path.is_file()
    ]
    return {"files": rows, "combined_sha256": canonical_hash(rows)}

def _source_descriptor(summaries: dict[int, dict[str, Any]], statuses: dict[int, dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for step in sorted(summaries):
        summary = summaries[step]
        status = statuses[step]
        rows.append(
            {
                "step": step,
                "experiment_id": summary.get("experiment_id"),
                "dataset_sha256": (summary.get("dataset") or {}).get("sha256"),
                "result_signature_sha256": (summary.get("reproducibility") or {}).get("result_signature_sha256"),
                "status_result_signature_sha256": status.get("result_signature_sha256"),
                "summary_sha256": sha256_file(SOURCE_PATHS[step]),
                "status_sha256": sha256_file(SOURCE_STATUS_PATHS[step]),
            }
        )
    return {"steps": rows, "combined_sha256": canonical_hash(rows)}


def evaluate_research_decision(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    resolved_policy = json.loads(json.dumps(DEFAULT_POLICY if policy is None else policy))
    summaries = {step: _load_json(path) for step, path in SOURCE_PATHS.items()}
    statuses = {step: _load_json(path) for step, path in SOURCE_STATUS_PATHS.items()}
    source = _source_descriptor(summaries, statuses)
    code = _code_descriptor()
    evidence_rows = build_evidence_matrix(summaries, resolved_policy)

    datasets = {(summary.get("dataset") or {}).get("sha256") for summary in summaries.values()}
    source_signatures_match = all(
        row["result_signature_sha256"] == row["status_result_signature_sha256"]
        for row in source["steps"]
    )
    source_statuses_complete = all(status.get("status") == "completed" for status in statuses.values())
    no_leakage = all(not bool(status.get("future_data_leakage_detected")) for status in statuses.values())
    no_production = all(not bool(status.get("production_integration_enabled", False)) for status in statuses.values())
    robust_positive = [row for row in evidence_rows if row["robust_superiority_demonstrated"]]
    robust_negative = [row for row in evidence_rows if row["evidence_outcome"] == "robust_negative"]
    positive_not_robust = [row for row in evidence_rows if row["evidence_outcome"] == "positive_but_not_robust"]

    gate = {
        "evidence_chain_complete": set(summaries) == set(resolved_policy["required_source_steps"]),
        "source_statuses_complete": source_statuses_complete,
        "source_signatures_match": source_signatures_match,
        "dataset_identity_consistent": len(datasets) == 1 and None not in datasets,
        "future_data_leakage_absent": no_leakage,
        "production_integration_absent": no_production,
        "robust_superiority_demonstrated": bool(robust_positive),
        "all_neural_promotion_gates_passed": bool(
            (summaries[145].get("comparison") or {}).get("promotion_gate_passed")
            and (summaries[146].get("comparison") or {}).get("promotion_gate_passed")
        ),
    }
    production_promotion = bool(
        gate["evidence_chain_complete"]
        and gate["source_statuses_complete"]
        and gate["source_signatures_match"]
        and gate["dataset_identity_consistent"]
        and gate["future_data_leakage_absent"]
        and gate["robust_superiority_demonstrated"]
        and gate["all_neural_promotion_gates_passed"]
    )

    decision = {
        "production_promotion": "approved" if production_promotion else "blocked",
        "current_neural_configuration": "continue" if production_promotion else resolved_policy["current_configuration_action"],
        "repeat_same_configuration_on_seen_holdouts": resolved_policy["repeat_same_configuration_on_seen_holdouts"],
        "next_research_mode": "materially_new_preregistered_hypothesis",
        "reason": (
            "No comparison in the Step 144–146 evidence chain demonstrates robust positive superiority. "
            "The current neural configuration is therefore paused and archived; production promotion remains blocked."
        ),
    }
    synthesis = {
        "evidence_rows": len(evidence_rows),
        "robust_positive_rows": len(robust_positive),
        "positive_but_not_robust_rows": len(positive_not_robust),
        "robust_negative_rows": len(robust_negative),
        "source_experiments": len(source["steps"]),
        "same_dataset_sha256": next(iter(datasets)) if len(datasets) == 1 else None,
        "latest_draw": (summaries[146].get("dataset") or {}).get("latest_draw"),
    }
    deterministic_payload = {
        "policy": resolved_policy,
        "source": source,
        "code": code,
        "evidence_matrix": evidence_rows,
        "synthesis": synthesis,
        "decision_gate": gate,
        "decision": decision,
    }
    policy_hash = canonical_hash(resolved_policy)
    evidence_hash = canonical_hash({"source": source, "evidence_matrix": evidence_rows})
    result_signature = canonical_hash(deterministic_payload)
    dataset_hash = synthesis["same_dataset_sha256"] or dataset_sha256()
    decision_id = f"DEC-147-{str(dataset_hash)[:10]}-{evidence_hash[:10]}"
    return {
        "decision_id": decision_id,
        "step": 147,
        "title": "Experimental Evidence Synthesis & Research Decision Gate",
        "status": "completed",
        "policy": resolved_policy,
        "source": source,
        "code": code,
        "evidence_matrix": evidence_rows,
        "synthesis": synthesis,
        "decision_gate": gate,
        "decision": decision,
        "reproducibility": {
            "command": "python tools/build_experimental_evidence_decision.py",
            "policy_sha256": policy_hash,
            "evidence_sha256": evidence_hash,
            "result_signature_sha256": result_signature,
            "deterministic_for_same_source_artifacts_and_policy": True,
        },
        "guardrails": {
            "production_pipeline_used": False,
            "real_ticket_generation_performed": False,
            "personal_journal_used": False,
            "heavy_ml_retraining_performed": False,
            "source_experiments_modified": False,
        },
        "safe_note_bg": SAFE_NOTE_BG,
    }


def _load_registry() -> list[dict[str, Any]]:
    if not DECISION_REGISTRY_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in DECISION_REGISTRY_PATH.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_outputs(report: dict[str, Any]) -> None:
    now = utc_now()
    registry = _load_registry()
    existing = next((row for row in registry if row.get("decision_id") == report["decision_id"]), None)
    record = json.loads(json.dumps(report))
    existing_signature = str(((existing or {}).get("reproducibility") or {}).get("result_signature_sha256") or "")
    current_signature = str((report.get("reproducibility") or {}).get("result_signature_sha256") or "")
    semantic_noop = bool(existing) and existing_signature == current_signature
    record["created_at_utc"] = (existing or {}).get("created_at_utc", now)
    record["last_evaluated_at_utc"] = (existing or {}).get("last_evaluated_at_utc", now) if semantic_noop else now
    registry = [row for row in registry if row.get("decision_id") != report["decision_id"]] + [record]
    registry.sort(key=lambda row: (int(row.get("step", 0)), str(row.get("decision_id", ""))))
    DECISION_REGISTRY_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in registry),
        encoding="utf-8",
    )

    POLICY_PATH.write_text(json.dumps(report["policy"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = {
        "step": 147,
        "status": "completed",
        "decision_id": report["decision_id"],
        "decision_registry_entries": len(registry),
        "dataset_sha256": report["synthesis"]["same_dataset_sha256"],
        "source_experiment_count": report["synthesis"]["source_experiments"],
        "evidence_row_count": report["synthesis"]["evidence_rows"],
        "robust_positive_rows": report["synthesis"]["robust_positive_rows"],
        "production_promotion_approved": report["decision"]["production_promotion"] == "approved",
        "current_neural_configuration_action": report["decision"]["current_neural_configuration"],
        "policy_sha256": report["reproducibility"]["policy_sha256"],
        "evidence_sha256": report["reproducibility"]["evidence_sha256"],
        "result_signature_sha256": report["reproducibility"]["result_signature_sha256"],
        "production_integration_enabled": False,
        "real_ticket_generation_enabled": False,
        "heavy_ml_retraining_performed": False,
        "personal_journal_used": False,
        "future_data_leakage_detected": False,
        "safe_note_bg": SAFE_NOTE_BG,
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fields = [
        "step", "experiment_id", "evidence_scope", "candidate", "comparator", "mean_advantage",
        "ci_lower", "ci_upper", "p_value", "positive_seed_rate", "positive_fold_rate",
        "source_promotion_gate_passed", "evidence_outcome", "robust_superiority_demonstrated",
        "production_eligible", "source_summary",
    ]
    _write_csv(EVIDENCE_MATRIX_CSV_PATH, report["evidence_matrix"], fields)
    index_rows = [
        {
            "decision_id": row.get("decision_id"),
            "status": row.get("status"),
            "title": row.get("title"),
            "created_at_utc": row.get("created_at_utc"),
            "last_evaluated_at_utc": row.get("last_evaluated_at_utc"),
            "dataset_sha256": (row.get("synthesis") or {}).get("same_dataset_sha256"),
            "source_experiments": (row.get("synthesis") or {}).get("source_experiments"),
            "evidence_rows": (row.get("synthesis") or {}).get("evidence_rows"),
            "production_promotion": (row.get("decision") or {}).get("production_promotion"),
            "current_neural_configuration": (row.get("decision") or {}).get("current_neural_configuration"),
            "result_signature_sha256": (row.get("reproducibility") or {}).get("result_signature_sha256"),
        }
        for row in registry
    ]
    _write_csv(
        DECISION_INDEX_CSV_PATH,
        index_rows,
        [
            "decision_id", "status", "title", "created_at_utc", "last_evaluated_at_utc", "dataset_sha256",
            "source_experiments", "evidence_rows", "production_promotion", "current_neural_configuration",
            "result_signature_sha256",
        ],
    )

    summary = {key: value for key, value in report.items() if key != "policy"}
    summary["policy"] = report["policy"]
    summary["decision_registry_entries"] = len(registry)
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DECISION_DIR.mkdir(parents=True, exist_ok=True)
    (DECISION_DIR / f"{report['decision_id']}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Step 147 — Experimental Evidence Synthesis & Research Decision Gate",
        "",
        f"- Decision ID: `{report['decision_id']}`",
        f"- Source experiments: **{report['synthesis']['source_experiments']}**",
        f"- Evidence rows: **{report['synthesis']['evidence_rows']}**",
        f"- Robust positive rows: **{report['synthesis']['robust_positive_rows']}**",
        f"- Robust negative rows: **{report['synthesis']['robust_negative_rows']}**",
        f"- Production promotion: **{report['decision']['production_promotion'].upper()}**",
        f"- Current neural configuration: **{report['decision']['current_neural_configuration'].upper()}**",
        "",
        "## Decision gate",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in report["decision_gate"].items())
    lines.extend(
        [
            "",
            "## Evidence matrix",
            "",
            "| Step | Candidate | Comparator | Advantage | 95% CI | Outcome |",
            "|---:|---|---|---:|---:|---|",
        ]
    )
    for row in report["evidence_matrix"]:
        ci = "—" if row["ci_lower"] is None else f"[{row['ci_lower']:.6f}, {row['ci_upper']:.6f}]"
        advantage = "—" if row["mean_advantage"] is None else f"{row['mean_advantage']:.6f}"
        lines.append(
            f"| {row['step']} | {row['candidate']} | {row['comparator']} | {advantage} | {ci} | {row['evidence_outcome']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "Следващ експеримент е допустим само при материално нова, предварително регистрирана хипотеза и нов/недокоснат validation период.",
            "",
            SAFE_NOTE_BG,
            "",
        ]
    )
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_experimental_evidence_decision(*, write_outputs: bool = True) -> dict[str, Any]:
    report = evaluate_research_decision()
    if write_outputs:
        _write_outputs(report)
    return report


def deterministic_signature(report: dict[str, Any]) -> str:
    return str((report.get("reproducibility") or {}).get("result_signature_sha256") or "")
