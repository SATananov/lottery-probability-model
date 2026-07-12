from __future__ import annotations

import ast
import hashlib
import json
import py_compile
import re
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v145_1_release_artifact_integrity import (
    ARCHIVE_ROOT_NAME,
    build_clean_zip,
    collect_release_rows,
    forbidden_release_reason,
    validate_release_manifest,
)
from src.v149_repository_hygiene_engine import (
    deterministic_status_signature,
    exact_duplicate_groups,
    repository_inventory,
    semantic_payload_sha256,
    sha256_file,
    write_semantic_version_snapshot,
)

REQUIRED = [
    ROOT / "AUTHORSHIP_AND_TOOLING.md",
    ROOT / "data/LOCAL_JOURNAL_README.md",
    ROOT / "data/user_journal_schema.sql",
    ROOT / "models/v149_repository_hygiene_policy.json",
    ROOT / "models/v149_repository_hygiene_status.json",
    ROOT / "reports/STEP_149_REPOSITORY_HYGIENE_PRIVACY_AND_AUTHORSHIP_TRANSPARENCY.md",
    ROOT / "reports/v149_repository_hygiene_summary.md",
    ROOT / "reports/v149_removed_current_tree_files.csv",
    ROOT / "reports/v149_remaining_exact_duplicate_groups.csv",
    ROOT / "src/v149_repository_hygiene_engine.py",
    ROOT / "tools/audit_repository_hygiene.py",
    ROOT / "tools/finalize_step_149_release.py",
    ROOT / "scripts/verify_step_149.py",
]

FROZEN_STEP148_REQUIRED = [
    "src/v145_experimental_neural_dynamics_engine.py",
    "src/v146_controlled_neural_robustness_engine.py",
    "src/v148_prospective_forward_test_engine.py",
    "models/v148_prospective_forward_test_policy.json",
    "models/v148_prospective_forward_test_status.json",
    "data/prospective_forward_test_ledger.jsonl",
    "reports/forward_tests/v148/LOCK-148-c299f383382d1f4a3ec7355f.json",
]

AI_RUNTIME_MODULES = {
    "openai",
    "anthropic",
    "langchain",
    "transformers",
    "tensorflow",
    "torch",
    "google.generativeai",
}


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object: {path}")
    return value


def snapshot() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(part in {".git", ".venv", "venv", ".r-lib", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        if rel == "data/user_journal.db" or rel.startswith("data/user_journal_exports/") or rel.startswith("reports/runtime/"):
            continue
        result[rel] = sha256_file(path)
    return result


def imported_top_level_modules(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def main() -> int:
    failures: list[str] = []
    before = snapshot()

    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"Missing: {path.relative_to(ROOT)}")

    for path in [item for item in REQUIRED if item.suffix == ".py"] + [
        ROOT / "src/data_importer.py",
        ROOT / "src/backtesting.py",
        ROOT / "src/cold_number_model.py",
        ROOT / "src/middle_number_model.py",
        ROOT / "src/gap_interval_model.py",
        ROOT / "src/prediction_engine.py",
        ROOT / "src/ml_extensions.py",
    ]:
        if path.is_file():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    if failures:
        for failure in failures:
            print("STEP_149_VERIFY_FAIL", failure)
        return 1

    policy = load_json(ROOT / "models/v149_repository_hygiene_policy.json")
    status = load_json(ROOT / "models/v149_repository_hygiene_status.json")
    release = load_json(ROOT / "release-manifest.json")

    if policy.get("step") != 149 or status.get("step") != 149 or status.get("status") != "completed":
        failures.append("Step 149 policy/status identity mismatch")
    if policy.get("history_rewrite_performed") is not False or status.get("history_rewrite_performed") is not False:
        failures.append("Step 149 must not rewrite Git history")
    if status.get("history_privacy_purge_completed") is not False or status.get("history_privacy_purge_deferred_to") != "Step 149.1":
        failures.append("Step 149.1 history-purge boundary is not recorded")
    if deterministic_status_signature(status) != status.get("result_signature_sha256"):
        failures.append("Step 149 status signature mismatch")

    checkpoint = str(release.get("checkpoint", ""))
    if checkpoint not in {"Step 149", "Step 150", "Step 150.1"}:
        failures.append(f"Unexpected release checkpoint: {checkpoint}")
    release_validation = validate_release_manifest(release, root=ROOT, expected_checkpoint=checkpoint)
    failures.extend(release_validation.get("failures", []))
    listed = {str(row.get("path")) for row in release.get("files", [])}
    for personal_path in ("data/user_journal.db", "data/user_journal_exports/"):
        if personal_path.endswith("/"):
            if any(item.startswith(personal_path) for item in listed):
                failures.append(f"Release manifest contains personal path: {personal_path}")
        elif personal_path in listed:
            failures.append(f"Release manifest contains personal path: {personal_path}")
    if forbidden_release_reason("data/user_journal.db") != "local_personal_data":
        failures.append("Journal database is not release-forbidden")
    if forbidden_release_reason("data/user_journal_exports/example.csv") is None:
        failures.append("Journal export directory is not release-forbidden")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for local_path in ("data/user_journal.db", "data/user_journal_exports/"):
        if local_path not in gitignore:
            failures.append(f"Local journal path missing from .gitignore: {local_path}")

    journal = ROOT / "data/user_journal.db"
    if journal.exists():
        try:
            with sqlite3.connect(journal) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                failures.append(f"Local journal integrity failed: {integrity}")
        except Exception as exc:
            failures.append(f"Local journal cannot be opened: {exc}")

    if (ROOT / "start_lottery_app_stable.bat").exists():
        failures.append("Duplicate stable launcher still exists")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "start_lottery_app_stable.bat" in readme:
        failures.append("README still references duplicate launcher")
    if "нежелани нежелани" in readme:
        failures.append("README repeated-word defect remains")
    for required_text in ("игнорирана от Git", "AUTHORSHIP_AND_TOOLING.md", "Step 149"):
        if required_text not in readme:
            failures.append(f"README Step 149 wording missing: {required_text}")
    launcher_text = (ROOT / "START_LOTTERY_CHROME_SIMPLE.bat").read_text(encoding="utf-8", errors="ignore")
    if "ne e nameren" in launcher_text or "Prati mi ekrana" in launcher_text:
        failures.append("Transliterated launcher messages remain")

    official = sorted((ROOT / "data/raw/bst_649_official").glob("*"))
    yearly = sorted((ROOT / "data/raw/bst_649_yearly").glob("*"))
    official_years = {
        int(match.group(1))
        for path in official
        if (match := re.fullmatch(r"649_(\d{4})\.txt", path.name))
    }
    yearly_years = {
        int(match.group(1))
        for path in yearly
        if (match := re.fullmatch(r"bst_649_(\d{4})\.(?:txt|docx)", path.name))
    }
    if official_years != set(range(1958, 2017)) or len(official) != 59:
        failures.append("Official raw source set is not canonical 1958-2016")
    if yearly_years != set(range(2017, 2026)) or len(yearly) != 9:
        failures.append("Yearly raw source set is not canonical 2017-2025")
    raw_hashes = [sha256_file(path) for path in official + yearly]
    if len(raw_hashes) != len(set(raw_hashes)):
        failures.append("Canonical raw source set still contains exact duplicates")
    importer_text = (ROOT / "src/data_importer.py").read_text(encoding="utf-8")
    if 'official_raw_dir = raw_dir.parent / "bst_649_official"' not in importer_text:
        failures.append("Importer does not combine canonical official and yearly directories")

    expected_versions = {
        "lottery_ml_extensions_model_v1_20260620_205905.json",
        "lottery_prediction_model_v36_20260620_205906.json",
    }
    actual_versions = {path.name for path in (ROOT / "models/versions").glob("*.json")}
    if actual_versions != expected_versions:
        failures.append(f"Unexpected model version snapshots: {sorted(actual_versions)}")
    semantic_states: set[str] = set()
    for path in [
        ROOT / "models/lottery_ml_extensions_model.json",
        ROOT / "models/lottery_prediction_model.json",
        *(ROOT / "models/versions").glob("*.json"),
    ]:
        semantic_states.add(semantic_payload_sha256(load_json(path)))
    if len(semantic_states) != 3:
        failures.append(f"Expected 3 semantic model states, got {len(semantic_states)}")
    with tempfile.TemporaryDirectory(prefix="step149_semantic_versions_") as tmp:
        directory = Path(tmp)
        payload = {"model": "test", "created_at": "2026-01-01", "value": 1}
        _, first_created = write_semantic_version_snapshot(payload, directory=directory, filename_prefix="test_model")
        _, duplicate_created = write_semantic_version_snapshot(
            {**payload, "created_at": "2026-01-02"}, directory=directory, filename_prefix="test_model"
        )
        _, changed_created = write_semantic_version_snapshot(
            {**payload, "created_at": "2026-01-03", "value": 2}, directory=directory, filename_prefix="test_model"
        )
        if first_created is not True or duplicate_created is not False or changed_created is not True:
            failures.append("Semantic model snapshot suppression is not deterministic")
        if len(list(directory.glob("*.json"))) != 2:
            failures.append("Semantic model snapshot test produced wrong file count")

    for name in ("backtest_report.md", "cold_backtest_report.md", "middle_backtest_report.md", "gap_backtest_report.md"):
        path = ROOT / "reports" / name
        text = path.read_text(encoding="utf-8")
        if path.stat().st_size > 10_000 or len(text.splitlines()) > 100:
            failures.append(f"Backtest Markdown is not compact: {name}")
        if "complete row-level table is intentionally not stored" not in text:
            failures.append(f"Backtest reproducibility note missing: {name}")

    inventory = repository_inventory(ROOT)
    expected_inventory = status.get("post_cleanup") or {}
    if checkpoint == "Step 149":
        for key in ("file_count", "duplicate_group_count", "duplicate_file_count", "duplicate_redundant_bytes"):
            if int(inventory.get(key, -1)) != int(expected_inventory.get(key, -2)):
                failures.append(f"Repository inventory mismatch: {key} {inventory.get(key)} != {expected_inventory.get(key)}")
    else:
        if int(inventory.get("file_count", -1)) < int(expected_inventory.get("file_count", 0)):
            failures.append("Later checkpoint unexpectedly removed files below the Step 149 baseline")
        for key in ("duplicate_group_count", "duplicate_file_count"):
            if int(inventory.get(key, 10**12)) > int(expected_inventory.get(key, -1)):
                failures.append(f"Repository hygiene regression: {key} {inventory.get(key)} > {expected_inventory.get(key)}")
    duplicate_groups = exact_duplicate_groups(ROOT)
    if any(any(path.startswith("data/raw/") for path in group["paths"]) for group in duplicate_groups):
        failures.append("Raw source duplicate group remains")
    if int(inventory.get("duplicate_group_count", 999)) > 35:
        failures.append("Unexpected increase in compatibility duplicate groups")

    requirements = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "requirements.txt", ROOT / "requirements-notebooks.txt")
    ).lower()
    for token in ("openai", "anthropic", "langchain", "transformers", "tensorflow", "torch"):
        if re.search(rf"(?m)^\s*{re.escape(token)}(?:[<>=~!\[]|\s|$)", requirements):
            failures.append(f"AI runtime dependency present: {token}")
    imported: set[str] = set()
    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        imported.update(imported_top_level_modules(path))
    for module in AI_RUNTIME_MODULES:
        if any(item == module or item.startswith(module + ".") for item in imported):
            failures.append(f"AI runtime import present: {module}")
    if status.get("explicit_vendor_marker_hits") != [] or status.get("external_generative_ai_runtime_dependency") is not False:
        failures.append("Step 149 authorship/runtime audit status is inconsistent")

    locks = policy.get("step148_immutable_locks") or {}
    if set(locks) != set(FROZEN_STEP148_REQUIRED):
        failures.append("Step 148 immutable lock set is incomplete")
    for relative, expected_hash in locks.items():
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            failures.append(f"Step 148 immutable artifact changed: {relative}")
    step148_status = load_json(ROOT / "models/v148_prospective_forward_test_status.json")
    if step148_status.get("active_lock_id") != status.get("active_forward_test_lock_id"):
        failures.append("Active Step 148 lock identity changed")

    checkpoint_metadata = {
        "Step 149": (ROOT / "CLEAN_ZIP_MANIFEST_STEP149.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP149.md"),
        "Step 150": (ROOT / "CLEAN_ZIP_MANIFEST_STEP150.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150.md"),
        "Step 150.1": (ROOT / "CLEAN_ZIP_MANIFEST_STEP150_1.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_1.md"),
    }
    metadata = checkpoint_metadata.get(checkpoint, checkpoint_metadata["Step 149"])
    if not all(path.is_file() for path in metadata):
        failures.append("Step 149 clean checkpoint metadata is missing")
    if not failures:
        with tempfile.TemporaryDirectory(prefix="step149_clean_zip_") as tmp:
            archive_path = Path(tmp) / "step149.zip"
            result = build_clean_zip(
                archive_path,
                root=ROOT,
                metadata_files=(ROOT / "release-manifest.json", metadata[0], metadata[1]),
            )
            if result.get("forbidden_entries"):
                failures.append("Step 149 clean ZIP contains forbidden entries")
            with zipfile.ZipFile(archive_path, "r") as archive:
                if archive.testzip() is not None:
                    failures.append("Step 149 clean ZIP CRC validation failed")
                names = archive.namelist()
                for forbidden in ("data/user_journal.db", "data/user_journal_exports/"):
                    if any(name.endswith(forbidden) or f"/{forbidden}" in name for name in names):
                        failures.append(f"Step 149 ZIP contains personal journal path: {forbidden}")
                if not all(Path(name).parts and Path(name).parts[0] == ARCHIVE_ROOT_NAME for name in names):
                    failures.append("Step 149 ZIP contains an entry outside the project root")

    after = snapshot()
    if before != after:
        changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        failures.append("Step 149 verification changed project files: " + ", ".join(changed[:20]))

    if failures:
        for failure in failures:
            print("STEP_149_VERIFY_FAIL", failure)
        return 1
    print("STEP_149_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
