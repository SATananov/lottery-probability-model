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
    ROOT / "src/v148_prospective_forward_test_engine.py",
    ROOT / "src/v148_prospective_forward_test_section.py",
    ROOT / "tools/lock_next_draw_forecast.py",
    ROOT / "tools/settle_locked_draw_forecast.py",
    ROOT / "tools/finalize_step_148_release.py",
    ROOT / "scripts/verify_step_148.py",
    ROOT / "models/v148_prospective_forward_test_policy.json",
    ROOT / "models/v148_prospective_forward_test_status.json",
    ROOT / "data/prospective_forward_test_ledger.jsonl",
    ROOT / "reports/v148_forward_test_summary.json",
    ROOT / "reports/v148_forward_test_summary.md",
    ROOT / "reports/v148_forward_test_ledger_index.csv",
    ROOT / "reports/v148_forward_test_settlements.csv",
    ROOT / "reports/v148_active_locked_evaluation_packages.csv",
    ROOT / "reports/STEP_148_PROSPECTIVE_FORWARD_TEST_LOCK_AND_UNTOUCHED_FUTURE_DRAW_LEDGER.md",
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


def validate_package(package: object, failures: list[str], label: str, expected_size: int) -> None:
    if not isinstance(package, list) or len(package) != expected_size:
        failures.append(f"Invalid package size: {label}")
        return
    seen: set[tuple[int, ...]] = set()
    for index, combo in enumerate(package, start=1):
        if not isinstance(combo, list):
            failures.append(f"Invalid combination type: {label}:{index}")
            continue
        values = tuple(int(value) for value in combo)
        if len(values) != 6 or len(set(values)) != 6 or tuple(sorted(values)) != values:
            failures.append(f"Invalid combination shape: {label}:{index}")
        if not all(1 <= value <= 49 for value in values):
            failures.append(f"Invalid combination range: {label}:{index}")
        if values in seen:
            failures.append(f"Duplicate combination: {label}:{index}")
        seen.add(values)


def main() -> int:
    failures: list[str] = []
    before = snapshot()

    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"Missing: {path.relative_to(ROOT)}")
    metadata_pairs = (
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP148.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP148.md"),
        (ROOT / "CLEAN_ZIP_MANIFEST_STEP149.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP149.md"),
    )
    if not any(all(path.is_file() for path in pair) for pair in metadata_pairs):
        failures.append("Missing Step 148 or later clean checkpoint manifests")

    for path in [item for item in REQUIRED if item.suffix == ".py"] + [ROOT / "streamlit_app.py"]:
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    if not failures:
        from src.v144_reproducible_experiment_registry_engine import dataset_descriptor, load_draws
        from src.v148_prospective_forward_test_engine import (
            METHOD_KEYS,
            active_lock,
            deterministic_forecast_signature_for_active_lock,
            ensure_policy,
            load_ledger,
            lock_next_draw_forecast,
            verify_ledger,
        )

        policy = load_json(ROOT / "models/v148_prospective_forward_test_policy.json")
        status = load_json(ROOT / "models/v148_prospective_forward_test_status.json")
        summary = load_json(ROOT / "reports/v148_forward_test_summary.json")
        step146 = load_json(ROOT / "models/v146_controlled_neural_robustness_status.json")
        step147 = load_json(ROOT / "models/v147_experimental_evidence_decision_status.json")
        draws = load_draws()
        dataset = dataset_descriptor(draws)
        events = load_ledger()
        chain = verify_ledger(events)
        lock = active_lock(events)

        if ensure_policy() != policy:
            failures.append("Stored Step 148 policy does not reproduce from frozen sources")
        if int(policy.get("step", 0)) != 148:
            failures.append("Step 148 policy step mismatch")
        protocol = policy.get("protocol") or {}
        if protocol.get("target_settled_draws") != 30 or protocol.get("milestones") != [10, 20, 30]:
            failures.append("Step 148 milestone protocol mismatch")
        if protocol.get("score_before_learn") is not True:
            failures.append("Step 148 score-before-learn is not required")
        if protocol.get("draws_without_predraw_lock_are_excluded") is not True:
            failures.append("Step 148 missing-lock exclusion is not enabled")
        guardrails = policy.get("guardrails") or {}
        for key, expected in (
            ("historical_backfill", "forbidden"),
            ("same_configuration_retuning", "forbidden"),
            ("parameter_changes_during_protocol", "forbidden"),
            ("personal_journal_access", "forbidden"),
            ("production_pipeline_access", "forbidden"),
            ("real_ticket_generation", "forbidden"),
        ):
            if guardrails.get(key) != expected:
                failures.append(f"Step 148 guardrail mismatch: {key}")

        frozen_code_locks = policy.get("frozen_code_locks") or {}
        for relative, expected_hash in frozen_code_locks.items():
            code_path = ROOT / str(relative)
            if not code_path.is_file() or file_hash(code_path) != expected_hash:
                failures.append(f"Frozen forward-scoring code lock mismatch: {relative}")
        if len(frozen_code_locks) != 3:
            failures.append("Step 148 frozen code lock set is incomplete")

        source_locks = policy.get("frozen_source_locks") or {}
        if source_locks.get("step146_configuration_sha256") != step146.get("configuration_sha256"):
            failures.append("Step 146 configuration lock mismatch")
        if source_locks.get("step146_result_signature_sha256") != step146.get("result_signature_sha256"):
            failures.append("Step 146 result lock mismatch")
        if source_locks.get("step147_result_signature_sha256") != step147.get("result_signature_sha256"):
            failures.append("Step 147 decision lock mismatch")
        if step147.get("production_promotion_approved") is not False:
            failures.append("Step 147 production block is no longer active")
        if step147.get("current_neural_configuration_action") != "pause_and_archive":
            failures.append("Step 147 neural archive decision changed")

        if not chain.get("ok"):
            failures.extend(f"Ledger integrity: {item}" for item in chain.get("failures", []))
        if chain.get("event_count") != 2:
            failures.append(f"Initial Step 148 checkpoint must contain 2 ledger events, got {chain.get('event_count')}")
        if chain.get("settled_count") != 0:
            failures.append("Initial Step 148 checkpoint must have zero settlements")
        if lock is None:
            failures.append("Initial Step 148 active lock is missing")
        else:
            if int(lock.get("source_dataset_rows", -1)) != len(draws):
                failures.append("Active lock dataset row count mismatch")
            if lock.get("source_dataset_sha256") != dataset.get("sha256"):
                failures.append("Active lock dataset SHA mismatch")
            if int(lock.get("target_sequence_index", 0)) != len(draws) + 1:
                failures.append("Active lock target sequence is not the next unseen draw")
            expected_key = f"{draws[-1]['year']}-{draws[-1]['draw_number'] + 1}"
            if lock.get("expected_draw_key") != expected_key:
                failures.append("Active lock expected draw key mismatch")
            artifact_path = ROOT / str(lock.get("artifact_path") or "")
            if artifact_path.is_file():
                artifact = load_json(artifact_path)
                commitment = artifact.get("forecast_commitment") or {}
                if commitment.get("lock_id") != lock.get("lock_id"):
                    failures.append("Active lock artifact ID mismatch")
                methods = commitment.get("methods") or {}
                package_size = int(protocol.get("evaluation_package_size", 0))
                for method in METHOD_KEYS:
                    entry = methods.get(method) or {}
                    validate_package(entry.get("evaluation_package"), failures, method, package_size)
                    ranking = entry.get("ranking")
                    if not isinstance(ranking, list) or sorted(int(value) for value in ranking) != list(range(1, 50)):
                        failures.append(f"Invalid full ranking: {method}")
                random_trials = commitment.get("uniform_random_trials")
                if not isinstance(random_trials, list) or len(random_trials) != int(protocol.get("uniform_random_trials", 0)):
                    failures.append("Uniform-random trial count mismatch")
                else:
                    for trial in random_trials:
                        validate_package(trial.get("evaluation_package"), failures, f"random:{trial.get('trial')}", package_size)
            reproduced = deterministic_forecast_signature_for_active_lock()
            if reproduced != lock.get("forecast_signature_sha256"):
                failures.append("Active locked forecast does not reproduce deterministically")

        if status.get("status") != "active" or int(status.get("step", 0)) != 148:
            failures.append("Step 148 status is not active")
        if status.get("protocol_id") != policy.get("protocol_id"):
            failures.append("Step 148 status protocol ID mismatch")
        if status.get("ledger_integrity_ok") is not True:
            failures.append("Step 148 status ledger integrity is not true")
        if int(status.get("eligible_settled_draws", -1)) != 0 or int(status.get("remaining_draws", -1)) != 30:
            failures.append("Step 148 initial progress mismatch")
        for key in (
            "production_promotion_approved", "automatic_production_promotion", "production_integration_enabled",
            "real_ticket_generation_enabled", "personal_journal_used", "historical_backfill_performed",
        ):
            if status.get(key) is not False:
                failures.append(f"Step 148 status guardrail is invalid: {key}")
        if summary.get("result_signature_sha256") != status.get("result_signature_sha256"):
            failures.append("Step 148 summary/status signature mismatch")
        if (summary.get("decision") or {}).get("production_promotion") != "blocked":
            failures.append("Step 148 production decision is not blocked")

        if len(read_csv(ROOT / "reports/v148_forward_test_settlements.csv")) != 0:
            failures.append("Initial settlement table must be empty")
        if len(read_csv(ROOT / "reports/v148_active_locked_evaluation_packages.csv")) != len(METHOD_KEYS) * int(protocol["evaluation_package_size"]):
            failures.append("Active evaluation package audit row count mismatch")

        release = load_json(ROOT / "release-manifest.json")
        if release.get("checkpoint") not in {"Step 148", "Step 149"}:
            failures.append(f"Unexpected release checkpoint: {release.get('checkpoint')}")
        listed = {str(row.get("path")) for row in release.get("files", [])}
        for required_path in (
            "scripts/verify_step_148.py",
            "tools/finalize_step_148_release.py",
            "tools/lock_next_draw_forecast.py",
            "tools/settle_locked_draw_forecast.py",
            "src/v148_prospective_forward_test_engine.py",
            "src/v148_prospective_forward_test_section.py",
            "data/prospective_forward_test_ledger.jsonl",
        ):
            if required_path not in listed:
                failures.append(f"Step 148 release manifest missing: {required_path}")

        streamlit_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        if "render_v148_prospective_forward_test_section" not in streamlit_text:
            failures.append("Step 148 UI import is missing")
        if '"Проспективен forward test"' not in streamlit_text:
            failures.append("Step 148 menu entry is missing")

        idempotent = lock_next_draw_forecast()
        if idempotent.get("created") is not False or idempotent.get("reason") != "active_lock_exists":
            failures.append("Repeated lock operation is not idempotent")

    after = snapshot()
    if before != after:
        changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        failures.append("Verification changed project files: " + ", ".join(changed[:20]))

    if failures:
        for failure in failures:
            print("STEP_148_VERIFY_FAIL", failure)
        return 1
    print("STEP_148_VERIFY_OK")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
