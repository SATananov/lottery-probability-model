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
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP150.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 150"
CHECKPOINT_TITLE = "Global Bulgarian UI, Table Localization & Technical Detail Separation"
BASE_COMMIT = "a1dc3e5"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def write_manifests() -> dict:
    for legacy in (
        ROOT / "CLEAN_ZIP_MANIFEST_STEP149.md",
        ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP149.md",
    ):
        legacy.unlink(missing_ok=True)

    rows = collect_release_rows(root=ROOT)
    status = load_json(ROOT / "models/v150_global_ui_polish_status.json")
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
            "ui_literal_rows": status.get("ui_literal_rows"),
            "unique_ui_literals": status.get("unique_ui_literals"),
            "forbidden_bulgarian_residual_rows": status.get("forbidden_bulgarian_residual_rows"),
            "mixed_language_rows": status.get("mixed_language_rows"),
            "mojibake_findings": status.get("mojibake_findings"),
            "technical_columns_hidden_by_default": status.get("technical_table_columns_hidden_by_default"),
            "technical_details_toggle": "v150_show_technical_details",
            "research_navigation_group": "🔬 Изследователски проверки",
            "deploy_button_hidden": status.get("deploy_button_hidden"),
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

    clean = f"""# CLEAN ZIP MANIFEST — STEP 150

- Project: `lottery-probability-model`
- Checkpoint: `Step 150 — {CHECKPOINT_TITLE}`
- Base code checkpoint: post-Step 149 privacy repair, commit `{BASE_COMMIT}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Step 150 verification: `STEP_150_VERIFY_OK`
- Bulgarian UI residual rows: **{status.get('forbidden_bulgarian_residual_rows', 'unknown')}**
- Mixed visible-language rows outside approved technical abbreviations: **{status.get('mixed_language_rows', 'unknown')}**
- Cyrillic/mojibake findings: **{status.get('mojibake_findings', 'unknown')}**
- Technical columns hidden by default: **Yes**
- Research navigation group: **Yes**
- Streamlit Deploy button hidden: **Yes**
- Personal `data/user_journal.db` included: **No**
- Personal `data/user_journal_exports/` included: **No**
- History rewrite performed: **No**
- Active Step 148 lock: `{step148.get('active_lock_id', 'unknown')}`
- Active expected draw: `{step148.get('active_expected_draw_key', 'unknown')}`
- Protected Step 148 files: **{'PASS' if (status.get('protected_step148_files') or {}).get('all_ok') else 'FAIL'}**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**

## Step 150 result

- One global display layer localizes module, page, menu and table UI.
- Research pages 144–148 use human labels and separate technical expanders.
- Internal IDs, SHA-256 signatures and UTC columns are hidden by default.
- A sidebar toggle exposes technical details when needed.
- UTF-8/Cyrillic integrity and visible-text literals are audited automatically.
- The active Step 148 lock and frozen scoring code remain unchanged.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = rf"""# Full CLEAN Checkpoint Manifest — Step 150

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 150 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{BASE_COMMIT}`
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Scope

- Applies one display-only language layer across the Streamlit module.
- Covers module-level widgets, sidebar, columns, containers, forms and tables.
- Separates user labels from technical identifiers and cryptographic signatures.
- Creates a dedicated research navigation group and interface-integrity page.
- Preserves personal journal privacy and Step 149 repository hygiene.
- Does not change model training, production scoring or Step 148 forward-test state.

## UI verification

- UI literal rows: `{status.get('ui_literal_rows', 'unknown')}`
- Unique UI literals: `{status.get('unique_ui_literals', 'unknown')}`
- Forbidden Bulgarian residual rows: `{status.get('forbidden_bulgarian_residual_rows', 'unknown')}`
- Mixed visible-language rows: `{status.get('mixed_language_rows', 'unknown')}`
- Mojibake findings: `{status.get('mojibake_findings', 'unknown')}`
- Technical fields hidden by default: `{status.get('technical_table_columns_hidden_by_default')}`
- Protected Step 148 files: `{(status.get('protected_step148_files') or {}).get('all_ok')}`
- Active lock: `{step148.get('active_lock_id', 'unknown')}`
- Expected draw: `{step148.get('active_expected_draw_key', 'unknown')}`

## Local checks

```powershell
python .\tools\audit_ui_language_integrity.py
python .\scripts\verify_step_148.py
python .\scripts\verify_step_149.py
python .\scripts\verify_step_150.py
python .\tools\finalize_step_150_release.py --verify-only
python .\tools\finalize_step_150_release.py --build-zip

git status -sb
```

When applying the clean ZIP, restore `.git`, `.venv` and the trusted local journal from the previous local backup. Journal paths remain ignored and excluded from release packages.
"""
    FULL_MANIFEST.write_text(full, encoding="utf-8")
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
    return ROOT.parent / f"lottery-probability-model_STEP150_GLOBAL-BULGARIAN-UI-TABLE-LOCALIZATION-TECHNICAL-DETAIL-SEPARATION_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 150 release metadata")
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
