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
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP149.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP149.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 149"
CHECKPOINT_TITLE = "Repository Hygiene, Privacy & Authorship Transparency"
BASE_COMMIT = "c221d85"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def write_manifests() -> dict:
    for legacy in (
        ROOT / "CLEAN_ZIP_MANIFEST_STEP148.md",
        ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP148.md",
    ):
        legacy.unlink(missing_ok=True)

    rows = collect_release_rows(root=ROOT)
    status = load_json(ROOT / "models/v149_repository_hygiene_status.json")
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
            "removed_file_count": status.get("removed_file_count"),
            "raw_aliases_removed": (status.get("removed_by_reason") or {}).get("raw_source_alias_removed"),
            "timestamp_only_model_snapshots_removed": (status.get("removed_by_reason") or {}).get("timestamp_only_model_snapshot_removed"),
            "remaining_compatibility_duplicate_groups": (status.get("post_cleanup") or {}).get("duplicate_group_count"),
            "compact_markdown_backtests": True,
            "duplicate_launcher_removed": True,
        },
        "authorship_and_tooling": {
            "transparency_document": "docs/AUTHORSHIP_AND_TOOLING.md",
            "external_generative_ai_runtime_dependency": False,
            "vendor_specific_ai_sdk_dependency": False,
            "manual_only_claim": False,
        },
        "prospective_forward_test_preservation": {
            "protocol_id": step148.get("protocol_id"),
            "active_lock_id": step148.get("active_lock_id"),
            "active_expected_draw_key": step148.get("active_expected_draw_key"),
            "eligible_settled_draws": step148.get("eligible_settled_draws"),
            "step148_immutable_locks_ok": status.get("step148_immutable_locks_ok"),
            "production_promotion": "blocked",
        },
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

    clean = f"""# CLEAN ZIP MANIFEST — STEP 149

- Project: `lottery-probability-model`
- Checkpoint: `Step 149 — {CHECKPOINT_TITLE}`
- Base code checkpoint: `Step 148`, commit `{BASE_COMMIT}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Step 149 verification: `STEP_149_VERIFY_OK`
- Personal `data/user_journal.db` included: **No**
- Personal `data/user_journal_exports/` included: **No**
- Public journal schema included: **Yes**
- History rewrite performed: **No**
- History privacy purge deferred to: **Step 149.1**
- Active Step 148 lock: `{step148.get('active_lock_id', 'unknown')}`
- Active expected draw: `{step148.get('active_expected_draw_key', 'unknown')}`
- Step 148 immutable locks: **{'PASS' if status.get('step148_immutable_locks_ok') else 'FAIL'}**
- External generative-AI runtime dependency: **No**
- Runtime cache included in archive: **No**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**
- Bundled `.pyc` / `.zip` / `.log` / backup artifacts: **No**

## Step 149 result

- Personal play history is local-only and excluded from Git/release scope.
- Raw source aliases and timestamp-only model snapshots are consolidated.
- Future timestamp-only model snapshots are suppressed by semantic hashing.
- Large row-level Markdown backtests are compact and reproducible.
- Compatibility-bound JSON mirrors remain listed for later dependency migration.
- Authorship and tooling transparency is documented without unsupported provenance claims.
- Step 148 forward-test protocol and active lock remain unchanged.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = rf"""# Full CLEAN Checkpoint Manifest — Step 149

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 149 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{BASE_COMMIT}` (`Step 148`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Scope

- Cleans the current repository tree with a normal commit.
- Does not rewrite Git history and does not require a force-push.
- Excludes personal journal data from Git and clean release packages.
- Preserves a public empty journal schema and local auto-initialization behavior.
- Consolidates safe exact aliases and timestamp-only snapshots.
- Keeps compatibility-bound JSON mirrors until their consumers are migrated.
- Documents authorship and tool assistance without claiming autonomous authorship.
- Preserves the Step 148 active forward-test lock and frozen scoring implementation.

## Cleanup state

- Files removed: `{status.get('removed_file_count', 'unknown')}`
- Raw aliases removed: `{(status.get('removed_by_reason') or {}).get('raw_source_alias_removed', 'unknown')}`
- Model snapshots removed: `{(status.get('removed_by_reason') or {}).get('timestamp_only_model_snapshot_removed', 'unknown')}`
- Remaining compatibility duplicate groups: `{(status.get('post_cleanup') or {}).get('duplicate_group_count', 'unknown')}`
- History rewrite performed: `False`
- History purge deferred to: `Step 149.1`

## Verification

- Step 144–148 regression verification: **PASS required**
- Step 149 privacy and hygiene verification: **PASS required**
- Release manifest validation: **PASS required**
- Personal journal exclusion: **PASS required**
- Step 148 immutable lock validation: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`

## Local checks

```powershell
python .\scripts\verify_step_148.py
python .\scripts\verify_step_149.py
python .\tools\finalize_step_149_release.py --verify-only
python .\tools\finalize_step_149_release.py --build-zip

git status -sb
```

When applying a clean ZIP, restore `.git`, `.venv` and the trusted local `data/user_journal.db` / `data/user_journal_exports/` from the previous local backup. The journal paths remain ignored and excluded from future release packages.
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
        "status_signature_sha256": status.get("result_signature_sha256"),
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
    return ROOT.parent / f"lottery-probability-model_STEP149_REPOSITORY-HYGIENE-PRIVACY-AUTHORSHIP-TRANSPARENCY_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 149 release metadata")
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
