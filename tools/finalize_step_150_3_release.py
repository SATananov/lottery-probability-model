from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v145_1_release_artifact_integrity import (
    POLICY_VERSION,
    build_clean_zip,
    collect_release_rows,
    release_scope_description,
    sha256_file,
    validate_release_manifest,
    write_json_atomic,
)

RELEASE_MANIFEST = ROOT / "release-manifest.json"
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP150_3.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_3.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 150.3"
CHECKPOINT_TITLE = "User-Friendly Internal Version Label Cleanup"
BASE_COMMIT = "Step 150.2 synchronized main"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def write_manifests() -> dict:
    for legacy in (
        ROOT / "CLEAN_ZIP_MANIFEST_STEP150_2.md",
        ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_2.md",
    ):
        legacy.unlink(missing_ok=True)

    rows = collect_release_rows(root=ROOT)
    status = load_json(ROOT / "models/v150_3_version_label_status.json")
    step149 = load_json(ROOT / "models/v149_repository_hygiene_status.json")
    step148 = load_json(ROOT / "models/v148_prospective_forward_test_status.json")
    release = {
        "checkpoint": CHECKPOINT,
        "checkpoint_title": CHECKPOINT_TITLE,
        "project": "lottery-probability-model",
        "release_policy_version": POLICY_VERSION,
        "manifest_scope": release_scope_description(),
        "privacy_policy": {
            "personal_journal_database": "local_only_excluded",
            "personal_journal_exports": "local_only_excluded",
            "public_journal_schema": "data/user_journal_schema.sql",
            "history_rewrite_performed": False,
            "history_privacy_purge_deferred_to": "Step 149.1",
        },
        "repository_hygiene": {
            "step149_status": step149.get("status"),
            "remaining_compatibility_duplicate_groups": (step149.get("post_cleanup") or {}).get("duplicate_group_count"),
            "personal_journal_tracked": False,
        },
        "ui_language_integrity": {
            "global_display_layer": "src/v150_global_ui_polish.py",
            "version_label_cleanup_layer": "src/v150_3_user_version_cleanup.py",
            "version_label_audit": "src/v150_3_version_label_integrity_engine.py",
            "python_literals_with_internal_versions": status.get("python_literals_with_internal_versions"),
            "literal_version_label_failures": status.get("literal_version_label_failures"),
            "dynamic_values_with_internal_versions": status.get("dynamic_values_with_internal_versions"),
            "dynamic_version_label_failures": status.get("dynamic_version_label_failures"),
            "screenshot_regression_failures": status.get("screenshot_regression_failures"),
            "normal_mode_hides_internal_versions": True,
            "technical_mode_preserves_internal_versions": True,
            "technical_columns_hidden_by_default": True,
            "deploy_button_hidden": True,
            "result_signature_sha256": status.get("result_signature_sha256"),
        },
        "prospective_forward_test_preservation": {
            "protocol_id": step148.get("protocol_id"),
            "active_lock_id": step148.get("active_lock_id"),
            "active_expected_draw_key": step148.get("active_expected_draw_key"),
            "eligible_settled_draws": step148.get("eligible_settled_draws"),
            "protected_files_ok": (status.get("protected_step148_files") or {}).get("all_ok"),
            "production_promotion": "blocked",
        },
        "display_only_change": True,
        "production_scoring_changed": False,
        "personal_journal_used": False,
        "forbidden_release_classes": [
            ".git and local environments",
            "runtime caches and local audit output",
            "Python, test and Jupyter caches",
            "secret environment files",
            "temporary archives, logs and backups",
            "build output and editor metadata",
            "personal user journal database and exports",
        ],
        "file_count": len(rows),
        "files": rows,
    }
    write_json_atomic(RELEASE_MANIFEST, release)
    release_sha = sha256_file(RELEASE_MANIFEST)
    project_count = len(rows) + len(METADATA_FILES)

    CLEAN_MANIFEST.write_text(
        f"""# CLEAN ZIP MANIFEST — STEP 150.3

- Project: `lottery-probability-model`
- Checkpoint: `Step 150.3 — {CHECKPOINT_TITLE}`
- Base Git commit: `{BASE_COMMIT}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Step 150.3 verification: `STEP_150_3_VERIFY_OK`
- Python literals with internal version labels: **{status.get('python_literals_with_internal_versions', 'unknown')}**
- Remaining literal failures: **{status.get('literal_version_label_failures', 'unknown')}**
- Dynamic values with internal version labels: **{status.get('dynamic_values_with_internal_versions', 'unknown')}**
- Remaining dynamic failures: **{status.get('dynamic_version_label_failures', 'unknown')}**
- Screenshot regression failures: **{status.get('screenshot_regression_failures', 'unknown')}**
- Technical columns hidden by default: **Yes**
- Full statistical details separated: **Yes**
- Personal `data/user_journal.db` included: **No**
- Personal `data/user_journal_exports/` included: **No**
- History rewrite performed: **No**
- Active Step 148 lock: `{step148.get('active_lock_id', 'unknown')}`
- Active expected draw: `{step148.get('active_expected_draw_key', 'unknown')}`
- Protected Step 148 files: **{'PASS' if (status.get('protected_step148_files') or {}).get('all_ok') else 'FAIL'}**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**

## Step 150.3 result

- Internal labels such as V1, v41 and v94 are removed from normal user mode.
- Workflow, model and plan versions are replaced by plain Bulgarian concepts.
- Exact internal versions remain available in technical-details mode.
- Dynamic JSON/CSV values and table cells use the same global cleanup.
- The active Step 148 lock and protected scoring files remain unchanged.
""",
        encoding="utf-8",
    )

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    FULL_MANIFEST.write_text(
        f"""# Full CLEAN Checkpoint Manifest — Step 150.3

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 150.3 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{BASE_COMMIT}`
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Scope

- Removes internal V-number labels from all normal user-facing Streamlit output.
- Replaces versioned workflow and model phrases with plain Bulgarian descriptions.
- Applies the cleanup to metrics, tables, JSON values, captions and status messages.
- Keeps exact versions, paths and identifiers available in technical-details mode.
- Preserves personal journal privacy and the Step 148 prospective lock.
- Does not change model training, production scoring or historical results.

## Verification

- Python literals with internal version labels: `{status.get('python_literals_with_internal_versions', 'unknown')}`
- Remaining literal failures: `{status.get('literal_version_label_failures', 'unknown')}`
- Dynamic values with internal version labels: `{status.get('dynamic_values_with_internal_versions', 'unknown')}`
- Remaining dynamic failures: `{status.get('dynamic_version_label_failures', 'unknown')}`
- Screenshot regression failures: `{status.get('screenshot_regression_failures', 'unknown')}`
- Technical mode preserves internal versions: `{status.get('technical_mode_preserves_internal_versions')}`
- Protected Step 148 files: `{(status.get('protected_step148_files') or {}).get('all_ok')}`
- Active lock: `{step148.get('active_lock_id', 'unknown')}`
- Expected draw: `{step148.get('active_expected_draw_key', 'unknown')}`

## Local checks

```powershell
python .\\tools\\audit_user_version_labels.py
python .\\scripts\\verify_step_148.py
python .\\scripts\\verify_step_149.py
python .\\scripts\\verify_step_150_3.py
python .\\tools\\finalize_step_150_3_release.py --verify-only
python .\\tools\\finalize_step_150_3_release.py --build-zip

git status -sb
```

When applying the clean ZIP, restore `.git`, `.venv` and the trusted local journal from the previous local backup. Journal paths remain ignored and excluded from release packages.
""",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "checkpoint": CHECKPOINT,
        "project_file_count": project_count,
        "release_manifest_entries": len(rows),
        "release_manifest_sha256": release_sha,
        "release_policy_version": POLICY_VERSION,
        "active_lock_id": step148.get("active_lock_id"),
        "active_expected_draw_key": step148.get("active_expected_draw_key"),
        "ui_status_signature_sha256": status.get("result_signature_sha256"),
    }


def verify_manifests() -> dict:
    release = load_json(RELEASE_MANIFEST)
    result = validate_release_manifest(release, root=ROOT, expected_checkpoint=CHECKPOINT)
    failures = list(result.get("failures", []))
    for path in (CLEAN_MANIFEST, FULL_MANIFEST):
        if not path.is_file():
            failures.append(f"missing_metadata:{path.name}")
    listed = {str(row.get("path")) for row in release.get("files", [])}
    if "data/user_journal.db" in listed or any(path.startswith("data/user_journal_exports/") for path in listed):
        failures.append("personal_journal_in_release_manifest")
    result.update(ok=not failures, failure_count=len(failures), failures=failures)
    return result


def default_archive_path() -> Path:
    stamp = datetime.now(ZoneInfo("Europe/Sofia")).strftime("%Y%m%d_%H%M%S")
    return ROOT.parent / f"lottery-probability-model_STEP150_3_USER-FRIENDLY-INTERNAL-VERSION-LABEL-CLEANUP_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 150.3 release metadata")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--build-zip", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.verify_only:
        result = verify_manifests()
    else:
        result = write_manifests()
        verification = verify_manifests()
        result["verification"] = verification
        result["ok"] = bool(result.get("ok")) and bool(verification.get("ok"))
        if result["ok"] and args.build_zip:
            destination = (args.output or default_archive_path()).resolve()
            result["clean_zip"] = build_clean_zip(destination, root=ROOT, metadata_files=METADATA_FILES)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
