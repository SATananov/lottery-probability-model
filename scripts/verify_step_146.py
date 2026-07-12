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
    ROOT / "src" / "v146_controlled_neural_robustness_engine.py",
    ROOT / "src" / "v146_controlled_neural_robustness_section.py",
    ROOT / "tools" / "run_controlled_neural_robustness.py",
    ROOT / "tools" / "finalize_step_146_release.py",
    ROOT / "models" / "v146_controlled_neural_robustness_policy.json",
    ROOT / "models" / "v146_controlled_neural_robustness_status.json",
    ROOT / "reports" / "v146_neural_robustness_run_results.csv",
    ROOT / "reports" / "v146_neural_robustness_seed_stability.csv",
    ROOT / "reports" / "v146_neural_robustness_fold_stability.csv",
    ROOT / "reports" / "v146_neural_robustness_draw_comparison.csv",
    ROOT / "reports" / "v146_neural_robustness_summary.json",
    ROOT / "reports" / "v146_neural_robustness_summary.md",
    ROOT / "reports" / "STEP_146_CONTROLLED_NEURAL_EXPERIMENT_EXPANSION_AND_ROBUSTNESS_VALIDATION.md",
    ROOT / "scripts" / "verify_step_146.py",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    failures: list[str] = []
    before = snapshot()

    for path in REQUIRED:
        if not path.exists():
            failures.append(f"Missing: {path.relative_to(ROOT)}")

    metadata_pairs = [
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP146.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP146.md"),
    ]
    if not any(all(path.exists() for path in pair) for pair in metadata_pairs):
        failures.append("Missing Step 146 clean checkpoint manifests")

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
        from src.v144_reproducible_experiment_registry_engine import DATASET_PATH, dataset_sha256
        from src.v146_controlled_neural_robustness_engine import (
            BASELINE_KEYS,
            DEFAULT_CONFIG,
            deterministic_signature,
            run_controlled_neural_robustness,
        )

        freshness = build_freshness_report(write_outputs=False)
        if freshness.get("overall_status") != "synced" or int(freshness.get("blocking_out_of_sync_count", -1)) != 0:
            failures.append("Step 143.3 zero-blocker state is not preserved")

        registry_rows = load_registry()
        ids = [str(row.get("experiment_id", "")) for row in registry_rows]
        if len(ids) != len(set(ids)):
            failures.append("Experiment registry contains duplicate IDs")
        step146_rows = [row for row in registry_rows if row.get("step") == 146]
        if len(step146_rows) != 1:
            failures.append(f"Expected one Step 146 registry row, got {len(step146_rows)}")
        else:
            experiment = step146_rows[0]
            if experiment.get("experiment_type") != "research_only_neural_robustness_validation":
                failures.append("Unexpected Step 146 experiment type")
            split = experiment.get("split_policy", {}) or {}
            if split.get("policy") != "expanding_window_walk_forward":
                failures.append("Unexpected Step 146 split policy")
            if split.get("robustness_design") != "three_non_overlapping_historical_folds_multi_seed":
                failures.append("Step 146 robustness design is missing")
            if split.get("target_draw_added_after_scoring") is not True:
                failures.append("Step 146 leakage guard is not confirmed")
            for key in (
                "heavy_ml_retraining_performed",
                "personal_journal_used",
                "future_data_leakage_detected",
                "production_pipeline_used",
                "real_ticket_generation_performed",
            ):
                if experiment.get(key) is not False:
                    failures.append(f"Step 146 experiment guardrail is invalid: {key}")

        status = load_json(ROOT / "models/v146_controlled_neural_robustness_status.json")
        if status.get("status") != "completed":
            failures.append(f"Invalid Step 146 status: {status.get('status')}")
        if status.get("dataset_sha256") != dataset_sha256(DATASET_PATH):
            failures.append("Step 146 dataset hash does not match canonical dataset")
        if int(status.get("fold_count", 0)) != int(DEFAULT_CONFIG["fold_count"]):
            failures.append("Step 146 fold count mismatch")
        if int(status.get("seed_count", 0)) != len(DEFAULT_CONFIG["seeds"]):
            failures.append("Step 146 seed count mismatch")
        if int(status.get("run_count", 0)) != int(DEFAULT_CONFIG["fold_count"]) * len(DEFAULT_CONFIG["seeds"]):
            failures.append("Step 146 run count mismatch")
        for key in (
            "production_integration_enabled",
            "real_ticket_generation_enabled",
            "heavy_ml_retraining_performed",
            "personal_journal_used",
            "future_data_leakage_detected",
        ):
            if status.get(key) is not False:
                failures.append(f"Step 146 status guardrail is invalid: {key}")

        policy = load_json(ROOT / "models/v146_controlled_neural_robustness_policy.json")
        if policy.get("step") != 146:
            failures.append("Step 146 policy step is invalid")
        robustness = policy.get("robustness_scope", {}) or {}
        for key in ("multi_seed", "non_overlapping_historical_folds", "bootstrap_confidence_intervals", "paired_sign_tests"):
            if robustness.get(key) is not True:
                failures.append(f"Step 146 robustness control missing: {key}")
        if (policy.get("promotion_gate", {}) or {}).get("automatic_promotion") is not False:
            failures.append("Step 146 automatic promotion must be disabled")

        summary = load_json(ROOT / "reports/v146_neural_robustness_summary.json")
        if summary.get("reproducibility", {}).get("result_signature_sha256") != status.get("result_signature_sha256"):
            failures.append("Step 146 summary and status signatures differ")
        split = summary.get("split_policy", {}) or {}
        expected_runs = int(DEFAULT_CONFIG["fold_count"]) * len(DEFAULT_CONFIG["seeds"])
        if int(split.get("run_count", 0)) != expected_runs:
            failures.append("Step 146 summary run count mismatch")
        if int(split.get("holdout_draws", 0)) != int(DEFAULT_CONFIG["fold_count"]) * int(DEFAULT_CONFIG["fold_size"]):
            failures.append("Step 146 distinct holdout draw count mismatch")
        comparison = summary.get("comparison", {}) or {}
        baseline_results = comparison.get("baselines", {}) or {}
        if set(baseline_results) != set(BASELINE_KEYS):
            failures.append(f"Unexpected Step 146 baselines: {sorted(baseline_results)}")
        for baseline, value in baseline_results.items():
            for key in (
                "mean_advantage",
                "bootstrap_ci_lower",
                "bootstrap_ci_upper",
                "two_sided_sign_test_p_value",
                "positive_seed_rate",
                "positive_fold_rate",
            ):
                if key not in value:
                    failures.append(f"Step 146 comparison missing {baseline}.{key}")
        if not isinstance(comparison.get("promotion_gate_passed"), bool):
            failures.append("Step 146 promotion result is missing")
        if (summary.get("diagnostics", {}) or {}).get("all_states_finite") is not True:
            failures.append("Step 146 neural state stability failed")

        run_rows = read_csv(ROOT / "reports/v146_neural_robustness_run_results.csv")
        seed_rows = read_csv(ROOT / "reports/v146_neural_robustness_seed_stability.csv")
        fold_rows = read_csv(ROOT / "reports/v146_neural_robustness_fold_stability.csv")
        draw_rows = read_csv(ROOT / "reports/v146_neural_robustness_draw_comparison.csv")
        if len(run_rows) != expected_runs:
            failures.append(f"Expected {expected_runs} Step 146 run rows, got {len(run_rows)}")
        if len(seed_rows) != len(DEFAULT_CONFIG["seeds"]):
            failures.append(f"Unexpected Step 146 seed rows: {len(seed_rows)}")
        if len(fold_rows) != int(DEFAULT_CONFIG["fold_count"]):
            failures.append(f"Unexpected Step 146 fold rows: {len(fold_rows)}")
        expected_draw_rows = expected_runs * int(DEFAULT_CONFIG["fold_size"])
        if len(draw_rows) != expected_draw_rows:
            failures.append(f"Expected {expected_draw_rows} Step 146 draw rows, got {len(draw_rows)}")

        rerun = run_controlled_neural_robustness(write_outputs=False, register=False)
        rerun_signature = deterministic_signature(rerun)
        if not rerun_signature or rerun_signature != status.get("result_signature_sha256"):
            failures.append("Step 146 read-only rerun does not reproduce stored signature")

        release = load_json(ROOT / "release-manifest.json")
        if release.get("checkpoint") != "Step 146":
            failures.append(f"Unexpected release checkpoint: {release.get('checkpoint')}")
        listed = {str(row.get("path")) for row in release.get("files", [])}
        for required_path in (
            "scripts/verify_step_146.py",
            "tools/finalize_step_146_release.py",
            "src/v146_controlled_neural_robustness_engine.py",
            "src/v146_controlled_neural_robustness_section.py",
        ):
            if required_path not in listed:
                failures.append(f"Step 146 release manifest missing: {required_path}")

        streamlit_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        if "render_v146_controlled_neural_robustness_section" not in streamlit_text:
            failures.append("Step 146 UI import is missing")
        if '"Контролирана neural robustness проверка"' not in streamlit_text:
            failures.append("Step 146 menu entry is missing")

    after = snapshot()
    if before != after:
        changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        failures.append("Verification changed project files: " + ", ".join(changed[:20]))

    if failures:
        for failure in failures:
            print("STEP_146_VERIFY_FAIL", failure)
        return 1
    print("STEP_146_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
