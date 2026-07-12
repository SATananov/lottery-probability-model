from __future__ import annotations

import csv
import hashlib
import json
import os
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = [
    ROOT / "src" / "v145_experimental_neural_dynamics_engine.py",
    ROOT / "src" / "v145_experimental_neural_dynamics_section.py",
    ROOT / "tools" / "run_experimental_neural_dynamics.py",
    ROOT / "tools" / "finalize_step_145_release.py",
    ROOT / "models" / "v145_experimental_neural_dynamics_policy.json",
    ROOT / "models" / "v145_experimental_neural_dynamics_status.json",
    ROOT / "reports" / "v145_neural_dynamics_results.csv",
    ROOT / "reports" / "v145_neural_dynamics_draw_comparison.csv",
    ROOT / "reports" / "v145_neural_dynamics_summary.json",
    ROOT / "reports" / "v145_neural_dynamics_summary.md",
    ROOT / "reports" / "STEP_145_EXPERIMENTAL_NEURAL_DYNAMICS_SANDBOX_AND_BASELINE_COMPARISON.md",
    ROOT / "scripts" / "verify_step_145.py",
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
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def load_registry() -> list[dict]:
    rows: list[dict] = []
    path = ROOT / "data" / "experiment_registry.jsonl"
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Registry line {line_number} is not an object")
        rows.append(value)
    return rows


def main() -> int:
    failures: list[str] = []
    before = snapshot()

    for path in REQUIRED:
        if not path.exists():
            failures.append(f"Missing: {path.relative_to(ROOT)}")

    metadata_pairs = [
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP145.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP145.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP145_1.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP145_1.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP146.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP146.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP147.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP147.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP148.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP148.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP149.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP149.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP150.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP150_1.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_1.md"),
    ]
    if not any(all(path.exists() for path in pair) for pair in metadata_pairs):
        failures.append("Missing Step 145 or Step 145.1 clean checkpoint manifests")

    compile_targets = [path for path in REQUIRED if path.suffix == ".py"] + [ROOT / "streamlit_app.py"]
    for path in compile_targets:
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    if not failures:
        from src.v122_unified_official_draw_freshness_engine import build_freshness_report
        from src.v145_experimental_neural_dynamics_engine import (
            DATASET_PATH,
            DEFAULT_CONFIG,
            deterministic_signature,
            dataset_sha256,
            run_experimental_neural_dynamics,
        )

        freshness = build_freshness_report(write_outputs=False)
        if freshness.get("overall_status") != "synced" or int(freshness.get("blocking_out_of_sync_count", -1)) != 0:
            failures.append("Step 143.3 zero-blocker state is not preserved")

        registry_rows = load_registry()
        ids = [str(row.get("experiment_id", "")) for row in registry_rows]
        if len(ids) != len(set(ids)):
            failures.append("Experiment registry contains duplicate IDs")
        step145_rows = [row for row in registry_rows if row.get("step") == 145]
        if len(step145_rows) != 1:
            failures.append(f"Expected one Step 145 registry row, got {len(step145_rows)}")
        else:
            experiment = step145_rows[0]
            if experiment.get("experiment_type") != "research_only_neural_dynamics_sandbox":
                failures.append("Unexpected Step 145 experiment type")
            split = experiment.get("split_policy", {}) or {}
            if split.get("policy") != "expanding_window_walk_forward":
                failures.append("Unexpected Step 145 split policy")
            if split.get("target_draw_added_after_scoring") is not True:
                failures.append("Step 145 leakage guard is not confirmed")
            if experiment.get("heavy_ml_retraining_performed") is not False:
                failures.append("Step 145 heavy ML guardrail is invalid")
            if experiment.get("personal_journal_used") is not False:
                failures.append("Step 145 personal journal guardrail is invalid")
            if experiment.get("future_data_leakage_detected") is not False:
                failures.append("Step 145 future leakage status is invalid")
            if experiment.get("production_pipeline_used") is not False:
                failures.append("Step 145 production isolation is invalid")
            if experiment.get("real_ticket_generation_performed") is not False:
                failures.append("Step 145 real-ticket guardrail is invalid")

        status = load_json(ROOT / "models" / "v145_experimental_neural_dynamics_status.json")
        if status.get("status") != "completed":
            failures.append(f"Invalid Step 145 status: {status.get('status')}")
        if status.get("dataset_sha256") != dataset_sha256(DATASET_PATH):
            failures.append("Step 145 dataset hash does not match canonical dataset")
        for key in (
            "production_integration_enabled",
            "real_ticket_generation_enabled",
            "heavy_ml_retraining_performed",
            "personal_journal_used",
            "future_data_leakage_detected",
        ):
            if status.get(key) is not False:
                failures.append(f"Step 145 status guardrail is invalid: {key}")

        policy = load_json(ROOT / "models" / "v145_experimental_neural_dynamics_policy.json")
        if policy.get("step") != 145:
            failures.append("Step 145 policy step is invalid")
        scope = policy.get("architecture_scope", {}) or {}
        if "analogue neural hardware" not in set(scope.get("not_implemented", [])):
            failures.append("Step 145 hardware non-claim is missing")
        if (policy.get("promotion_gate", {}) or {}).get("automatic_promotion") is not False:
            failures.append("Step 145 automatic promotion must be disabled")

        summary = load_json(ROOT / "reports" / "v145_neural_dynamics_summary.json")
        if summary.get("reproducibility", {}).get("result_signature_sha256") != status.get("result_signature_sha256"):
            failures.append("Step 145 summary and status signatures differ")
        architecture = summary.get("architecture", {}) or {}
        if architecture.get("production_integration") is not False:
            failures.append("Step 145 architecture is not isolated from production")
        diagnostics = summary.get("diagnostics", {}) or {}
        if diagnostics.get("all_states_finite") is not True:
            failures.append("Step 145 neural state stability check failed")
        comparison = summary.get("comparison", {}) or {}
        if not isinstance(comparison.get("promotion_gate_passed"), bool):
            failures.append("Step 145 promotion gate result is missing")

        with (ROOT / "reports" / "v145_neural_dynamics_results.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            result_rows = list(csv.DictReader(handle))
        expected_rows = 3 + int(DEFAULT_CONFIG["random_trials"])
        if len(result_rows) != expected_rows:
            failures.append(f"Expected {expected_rows} Step 145 result rows, got {len(result_rows)}")
        strategies = {row.get("strategy") for row in result_rows}
        expected_strategies = {
            "neural_dynamics_reservoir",
            "frequency_walk_forward",
            "recency_weighted_walk_forward",
            "uniform_random",
        }
        if strategies != expected_strategies:
            failures.append(f"Unexpected Step 145 strategies: {strategies}")

        with (ROOT / "reports" / "v145_neural_dynamics_draw_comparison.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            draw_rows = list(csv.DictReader(handle))
        if len(draw_rows) != int(DEFAULT_CONFIG["holdout_draws"]):
            failures.append(f"Unexpected Step 145 draw comparison count: {len(draw_rows)}")

        run_a = run_experimental_neural_dynamics(write_outputs=False, register=False)
        run_b = run_experimental_neural_dynamics(write_outputs=False, register=False)
        signature_a = deterministic_signature(run_a)
        signature_b = deterministic_signature(run_b)
        if not signature_a or signature_a != signature_b:
            failures.append("Repeated Step 145 read-only runs are not deterministic")
        if signature_a != status.get("result_signature_sha256"):
            failures.append("Step 145 read-only rerun does not reproduce stored signature")

        release = load_json(ROOT / "release-manifest.json")
        if release.get("checkpoint") not in {"Step 145", "Step 145.1", "Step 146", "Step 147", "Step 148", "Step 149", "Step 150", "Step 150.1"}:
            failures.append(f"Unexpected release checkpoint: {release.get('checkpoint')}")
        listed = {str(row.get("path")) for row in release.get("files", [])}
        for required_path in (
            "scripts/verify_step_145.py",
            "tools/finalize_step_145_release.py",
            "src/v145_experimental_neural_dynamics_engine.py",
        ):
            if required_path not in listed:
                failures.append(f"Step 145 release manifest missing: {required_path}")

        streamlit_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        if "render_v145_experimental_neural_dynamics_section" not in streamlit_text:
            failures.append("Step 145 UI import is missing")
        if '"Лаборатория за невронна динамика"' not in streamlit_text:
            failures.append("Step 145 menu entry is missing")

    after = snapshot()
    if before != after:
        changed = sorted(set(before) | set(after))
        changed = [path for path in changed if before.get(path) != after.get(path)]
        failures.append("Verification changed project files: " + ", ".join(changed[:20]))

    if failures:
        for failure in failures:
            print("STEP_145_VERIFY_FAIL", failure)
        return 1
    print("STEP_145_VERIFY_OK")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
