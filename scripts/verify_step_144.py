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
    ROOT / "src" / "v144_reproducible_experiment_registry_engine.py",
    ROOT / "src" / "v144_reproducible_experiment_registry_section.py",
    ROOT / "tools" / "run_reproducible_baseline_experiment.py",
    ROOT / "tools" / "finalize_step_144_release.py",
    ROOT / "data" / "experiment_registry.jsonl",
    ROOT / "models" / "v144_reproducible_experiment_registry_policy.json",
    ROOT / "models" / "v144_reproducible_experiment_registry_status.json",
    ROOT / "reports" / "v144_experiment_registry_index.csv",
    ROOT / "reports" / "v144_baseline_lab_results.csv",
    ROOT / "reports" / "v144_baseline_lab_summary.json",
    ROOT / "reports" / "v144_baseline_lab_summary.md",
    ROOT / "reports" / "STEP_144_REPRODUCIBLE_EXPERIMENT_REGISTRY_AND_BASELINE_LABORATORY.md",
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


def main() -> int:
    failures: list[str] = []
    before = snapshot()

    for path in REQUIRED:
        if not path.exists():
            failures.append(f"Missing: {path.relative_to(ROOT)}")

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
        from src.v144_reproducible_experiment_registry_engine import (
            DATASET_PATH,
            DEFAULT_CONFIG,
            deterministic_signature,
            dataset_sha256,
            run_reproducible_baseline_experiment,
        )

        freshness = build_freshness_report(write_outputs=False)
        if freshness.get("overall_status") != "synced" or int(freshness.get("blocking_out_of_sync_count", -1)) != 0:
            failures.append("Step 143.3 zero-blocker state is not preserved")

        registry_rows: list[dict] = []
        for line_number, line in enumerate((ROOT / "data" / "experiment_registry.jsonl").read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception as exc:
                failures.append(f"Registry JSONL line {line_number}: {exc}")
                continue
            if not isinstance(row, dict):
                failures.append(f"Registry line {line_number} is not an object")
                continue
            registry_rows.append(row)

        ids = [str(row.get("experiment_id", "")) for row in registry_rows]
        if not ids or any(not value for value in ids):
            failures.append("Registry has no valid experiment ID")
        if len(ids) != len(set(ids)):
            failures.append("Registry contains duplicate experiment IDs")

        required_fields = set(load_json(ROOT / "models" / "v144_reproducible_experiment_registry_policy.json").get("required_registry_fields", []))
        for row in registry_rows:
            missing = sorted(required_fields - set(row))
            if missing:
                failures.append(f"Registry experiment {row.get('experiment_id')} missing fields: {missing}")
            split = row.get("split_policy", {}) or {}
            if split.get("policy") != "expanding_window_walk_forward":
                failures.append("Unexpected split policy")
            if split.get("target_draw_added_after_scoring") is not True:
                failures.append("Leakage guard is not confirmed")
            if row.get("heavy_ml_retraining_performed") is not False:
                failures.append("Heavy ML retraining guardrail is not false")
            if row.get("personal_journal_used") is not False:
                failures.append("Personal journal guardrail is not false")
            if row.get("future_data_leakage_detected") is not False:
                failures.append("Future-data leakage status is not false")

        status = load_json(ROOT / "models" / "v144_reproducible_experiment_registry_status.json")
        if status.get("status") != "completed":
            failures.append(f"Invalid Step 144 status: {status.get('status')}")
        if status.get("dataset_sha256") != dataset_sha256(DATASET_PATH):
            failures.append("Status dataset hash does not match canonical dataset")
        if status.get("heavy_ml_retraining_performed") is not False:
            failures.append("Status heavy-ML guardrail is invalid")
        if status.get("future_data_leakage_detected") is not False:
            failures.append("Status leakage guardrail is invalid")

        summary = load_json(ROOT / "reports" / "v144_baseline_lab_summary.json")
        if summary.get("reproducibility", {}).get("result_signature_sha256") != status.get("result_signature_sha256"):
            failures.append("Summary and status result signatures differ")
        if int(summary.get("split_policy", {}).get("holdout_draws", 0)) != int(DEFAULT_CONFIG["holdout_draws"]):
            failures.append("Default holdout size is not recorded")

        with (ROOT / "reports" / "v144_baseline_lab_results.csv").open("r", encoding="utf-8-sig", newline="") as handle:
            result_rows = list(csv.DictReader(handle))
        expected_rows = 1 + int(DEFAULT_CONFIG["random_trials"])
        if len(result_rows) != expected_rows:
            failures.append(f"Expected {expected_rows} baseline rows, got {len(result_rows)}")
        strategies = {row.get("strategy") for row in result_rows}
        if strategies != {"frequency_walk_forward", "uniform_random"}:
            failures.append(f"Unexpected baseline strategies: {strategies}")

        run_a = run_reproducible_baseline_experiment(write_outputs=False, register=False)
        run_b = run_reproducible_baseline_experiment(write_outputs=False, register=False)
        signature_a = deterministic_signature(run_a)
        signature_b = deterministic_signature(run_b)
        if not signature_a or signature_a != signature_b:
            failures.append("Repeated read-only runs are not deterministic")
        if signature_a != status.get("result_signature_sha256"):
            failures.append("Read-only rerun does not reproduce stored result signature")


        release = load_json(ROOT / "release-manifest.json")
        listed = {str(row.get("path")) for row in release.get("files", [])}
        checkpoint = str(release.get("checkpoint", ""))
        if checkpoint not in {"Step 144", "Step 145", "Step 145.1", "Step 146", "Step 147", "Step 148", "Step 149"}:
            failures.append(f"Unexpected release checkpoint: {checkpoint}")
        if "scripts/verify_step_144.py" not in listed or "tools/finalize_step_144_release.py" not in listed:
            failures.append("Step 144 release manifest is incomplete")

        streamlit_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        if "render_v144_reproducible_experiment_registry_section" not in streamlit_text:
            failures.append("Step 144 UI import is missing")
        if '"Регистър на възпроизводимите експерименти"' not in streamlit_text:
            failures.append("Step 144 menu entry is missing")

    after = snapshot()
    if before != after:
        changed = sorted(set(before) | set(after))
        changed = [path for path in changed if before.get(path) != after.get(path)]
        failures.append("Verification changed project files: " + ", ".join(changed[:20]))

    if failures:
        for failure in failures:
            print("STEP_144_VERIFY_FAIL", failure)
        return 1
    print("STEP_144_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
