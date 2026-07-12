from __future__ import annotations

import csv
import hashlib
import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = [
    ROOT / "src/v147_experimental_evidence_decision_engine.py",
    ROOT / "src/v147_experimental_evidence_decision_section.py",
    ROOT / "tools/build_experimental_evidence_decision.py",
    ROOT / "tools/finalize_step_147_release.py",
    ROOT / "scripts/verify_step_147.py",
    ROOT / "models/v147_experimental_evidence_decision_policy.json",
    ROOT / "models/v147_experimental_evidence_decision_status.json",
    ROOT / "data/research_decision_registry.jsonl",
    ROOT / "reports/v147_research_decision_registry_index.csv",
    ROOT / "reports/v147_experimental_evidence_matrix.csv",
    ROOT / "reports/v147_research_decision_summary.json",
    ROOT / "reports/v147_research_decision_summary.md",
    ROOT / "reports/STEP_147_EXPERIMENTAL_EVIDENCE_SYNTHESIS_AND_RESEARCH_DECISION_GATE.md",
]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot() -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): file_hash(path)
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and "reports/runtime" not in path.as_posix()
        and path.suffix != ".pyc"
    }


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_registry() -> list[dict]:
    rows: list[dict] = []
    for line in (ROOT / "data/research_decision_registry.jsonl").read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("Research decision registry contains a non-object row")
            rows.append(value)
    return rows


def main() -> int:
    failures: list[str] = []
    before = snapshot()

    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"Missing: {path.relative_to(ROOT)}")
    metadata_pairs = [
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP147.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP147.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP148.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP148.md"),
    ]
    if not any(all(path.is_file() for path in pair) for pair in metadata_pairs):
        failures.append("Missing Step 147 or later clean checkpoint manifests")

    for path in [item for item in REQUIRED if item.suffix == ".py"] + [ROOT / "streamlit_app.py"]:
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    if not failures:
        from src.v144_reproducible_experiment_registry_engine import DATASET_PATH, dataset_sha256
        from src.v147_experimental_evidence_decision_engine import deterministic_signature, evaluate_research_decision

        status = load_json(ROOT / "models/v147_experimental_evidence_decision_status.json")
        policy = load_json(ROOT / "models/v147_experimental_evidence_decision_policy.json")
        summary = load_json(ROOT / "reports/v147_research_decision_summary.json")
        evidence_rows = read_csv(ROOT / "reports/v147_experimental_evidence_matrix.csv")
        registry_rows = load_registry()

        if status.get("status") != "completed" or int(status.get("step", 0)) != 147:
            failures.append("Step 147 status is not completed")
        if status.get("dataset_sha256") != dataset_sha256(DATASET_PATH):
            failures.append("Step 147 dataset identity mismatch")
        if status.get("production_promotion_approved") is not False:
            failures.append("Step 147 production promotion must remain blocked")
        if status.get("current_neural_configuration_action") != "pause_and_archive":
            failures.append("Step 147 current neural configuration action is invalid")
        for key in (
            "production_integration_enabled",
            "real_ticket_generation_enabled",
            "heavy_ml_retraining_performed",
            "personal_journal_used",
            "future_data_leakage_detected",
        ):
            if status.get(key) is not False:
                failures.append(f"Step 147 status guardrail is invalid: {key}")

        if policy.get("required_source_steps") != [144, 145, 146]:
            failures.append("Step 147 source-step policy mismatch")
        if policy.get("repeat_same_configuration_on_seen_holdouts") != "forbidden":
            failures.append("Step 147 repeated holdout tuning is not forbidden")
        if policy.get("current_configuration_action") != "pause_and_archive":
            failures.append("Step 147 policy does not pause the current configuration")
        requirements = set(policy.get("next_experiment_requirements", []))
        for required in (
            "materially_new_hypothesis",
            "preregistered_primary_metric_and_gate",
            "untouched_or_future_validation_period",
            "no_production_pipeline_access",
        ):
            if required not in requirements:
                failures.append(f"Step 147 next-experiment requirement missing: {required}")

        if summary.get("decision_id") != status.get("decision_id"):
            failures.append("Step 147 summary and status decision IDs differ")
        if (summary.get("reproducibility") or {}).get("result_signature_sha256") != status.get("result_signature_sha256"):
            failures.append("Step 147 summary and status signatures differ")
        synthesis = summary.get("synthesis", {}) or {}
        if int(synthesis.get("source_experiments", 0)) != 3:
            failures.append("Step 147 source experiment count mismatch")
        if int(synthesis.get("evidence_rows", 0)) != 9 or len(evidence_rows) != 9:
            failures.append("Step 147 evidence matrix row count mismatch")
        if int(synthesis.get("robust_positive_rows", -1)) != 0:
            failures.append("Step 147 unexpectedly claims robust positive evidence")
        if int(synthesis.get("robust_negative_rows", 0)) < 1:
            failures.append("Step 147 robust negative evidence is missing")
        decision = summary.get("decision", {}) or {}
        if decision.get("production_promotion") != "blocked":
            failures.append("Step 147 production decision is not blocked")
        if decision.get("current_neural_configuration") != "pause_and_archive":
            failures.append("Step 147 neural research decision is invalid")
        gate = summary.get("decision_gate", {}) or {}
        for key in (
            "evidence_chain_complete",
            "source_statuses_complete",
            "source_signatures_match",
            "dataset_identity_consistent",
            "future_data_leakage_absent",
            "production_integration_absent",
        ):
            if gate.get(key) is not True:
                failures.append(f"Step 147 evidence integrity gate failed: {key}")
        for key in ("robust_superiority_demonstrated", "all_neural_promotion_gates_passed"):
            if gate.get(key) is not False:
                failures.append(f"Step 147 decision gate must be false: {key}")

        if len(registry_rows) != 1:
            failures.append(f"Expected one Step 147 decision registry row, got {len(registry_rows)}")
        elif registry_rows[0].get("decision_id") != status.get("decision_id"):
            failures.append("Step 147 decision registry ID mismatch")

        rerun = evaluate_research_decision()
        if deterministic_signature(rerun) != status.get("result_signature_sha256"):
            failures.append("Step 147 read-only synthesis does not reproduce stored signature")

        release = load_json(ROOT / "release-manifest.json")
        if release.get("checkpoint") not in {"Step 147", "Step 148"}:
            failures.append(f"Unexpected release checkpoint: {release.get('checkpoint')}")
        listed = {str(row.get("path")) for row in release.get("files", [])}
        for required_path in (
            "scripts/verify_step_147.py",
            "tools/finalize_step_147_release.py",
            "src/v147_experimental_evidence_decision_engine.py",
            "src/v147_experimental_evidence_decision_section.py",
            "data/research_decision_registry.jsonl",
        ):
            if required_path not in listed:
                failures.append(f"Step 147 release manifest missing: {required_path}")

        streamlit_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        if "render_v147_experimental_evidence_decision_section" not in streamlit_text:
            failures.append("Step 147 UI import is missing")
        if '"Research decision gate"' not in streamlit_text:
            failures.append("Step 147 menu entry is missing")

    after = snapshot()
    if before != after:
        changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        failures.append("Verification changed project files: " + ", ".join(changed[:20]))

    if failures:
        for failure in failures:
            print("STEP_147_VERIFY_FAIL", failure)
        return 1
    print("STEP_147_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
