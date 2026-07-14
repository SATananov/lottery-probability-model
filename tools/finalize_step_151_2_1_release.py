from __future__ import annotations

import argparse
import json
import subprocess
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
from src.v151_2_repository_sync_integrity_engine import audit_repository_sync, write_artifacts as write_step151_2_artifacts
from src.v151_2_1_user_backup_ui_integrity_engine import (
    CHECKPOINT,
    CHECKPOINT_TITLE,
    audit_user_backup_ui,
    write_artifacts as write_step151_2_1_artifacts,
)

RELEASE_MANIFEST = ROOT / "release-manifest.json"
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP151_2_1.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151_2_1.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)


def _git_head() -> dict[str, str]:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
        subject = subprocess.check_output(["git", "log", "-1", "--pretty=%s", "HEAD"], cwd=ROOT, text=True).strip()
        return {"sha": sha, "subject": subject}
    except Exception:
        return {"sha": "unknown", "subject": "unknown"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def _remove_legacy_metadata() -> list[str]:
    keep = {CLEAN_MANIFEST.name, FULL_MANIFEST.name}
    removed: list[str] = []
    for pattern in ("CLEAN_ZIP_MANIFEST_STEP*.md", "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP*.md"):
        for path in ROOT.glob(pattern):
            if path.name not in keep:
                path.unlink(missing_ok=True)
                removed.append(path.name)
    return sorted(set(removed))


def write_manifests() -> dict:
    removed = _remove_legacy_metadata()
    write_step151_2_artifacts()
    write_step151_2_1_artifacts()

    repository = audit_repository_sync()
    backup_ui = audit_user_backup_ui()
    if not repository.get("ok") or not backup_ui.get("ok"):
        return {
            "ok": False,
            "reason": "step151_2_1_audit_failed",
            "repository": repository,
            "backup_ui": backup_ui,
        }

    rows = collect_release_rows(root=ROOT)
    parent = _git_head()
    step148 = _load_json(ROOT / "models/v148_prospective_forward_test_status.json")
    release = {
        "checkpoint": CHECKPOINT,
        "checkpoint_title": CHECKPOINT_TITLE,
        "project": "lottery-probability-model",
        "release_policy_version": POLICY_VERSION,
        "manifest_scope": release_scope_description(),
        "parent_git": parent,
        "repository_sync": repository.get("git"),
        "line_endings": repository.get("line_endings"),
        "ui_runtime_repairs": repository.get("ui_repairs"),
        "user_backup_ui": backup_ui,
        "fresh_clone_verification_command": "python scripts/verify_step_151_2_1.py --require-synced",
        "external_github_push_asserted": False,
        "prospective_forward_test": {
            "status": step148.get("status"),
            "eligible_settled_draws": step148.get("eligible_settled_draws"),
            "target_settled_draws": step148.get("target_settled_draws"),
            "active_lock_id": step148.get("active_lock_id"),
            "active_expected_draw_key": step148.get("active_expected_draw_key"),
            "production_promotion_approved": step148.get("production_promotion_approved"),
        },
        "privacy_policy": {
            "personal_journal_database": "local_only_excluded",
            "personal_journal_exports": "local_only_excluded",
        },
        "legacy_release_metadata_removed": removed,
        "display_only": True,
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
        "personal_journal_used": False,
        "result_signature_sha256": backup_ui.get("result_signature_sha256"),
        "file_count": len(rows),
        "files": rows,
    }
    write_json_atomic(RELEASE_MANIFEST, release)
    release_sha = sha256_file(RELEASE_MANIFEST)

    git = repository["git"]
    eol = repository["line_endings"]
    CLEAN_MANIFEST.write_text(
        f"""# CLEAN ZIP MANIFEST — STEP 151.2.1

- Project: `lottery-probability-model`
- Checkpoint: `{CHECKPOINT} — {CHECKPOINT_TITLE}`
- Parent Git commit: `{parent['sha']} {parent['subject']}`
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Canonical LF index: **{'Yes' if eol.get('canonical_index_lf') else 'No'}**
- Canonical LF working tree: **{'Yes' if eol.get('canonical_worktree_lf') else 'No'}**
- User-facing backup UI: **{'OK' if backup_ui.get('ok') else 'CHECK REQUIRED'}**
- Unguarded raw technical outputs: **{len(backup_ui.get('unguarded_raw_technical_outputs', []))}**
- Local branch: `{git.get('branch')}`
- Ahead / behind local upstream snapshot: `{git.get('ahead')}` / `{git.get('behind')}`
- External GitHub push asserted by builder: **No**
- Personal journal database included: **No**
- Personal journal exports included: **No**
- Bundled `.git`, `.venv` and caches: **No**

The archive is push-ready. Final synchronization is accepted only after `git push origin main` and `python scripts/verify_step_151_2_1.py --require-synced` pass on the operator machine.
""",
        encoding="utf-8",
        newline="\n",
    )

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    FULL_MANIFEST.write_text(
        f"""# Full CLEAN Checkpoint Manifest — Step 151.2.1

## Project

- Generated: `{generated}`
- Parent Git: `{parent['sha']} {parent['subject']}`
- Checkpoint: `{CHECKPOINT} — {CHECKPOINT_TITLE}`
- Release policy: `{POLICY_VERSION}`

## Closed items

- the Step 103 page is presented as **Application backup** in normal mode;
- the purpose, readiness state, archive contents and GitHub prerequisite are explained in plain language;
- raw Git status, terminal command, internal checks, paths and result dictionaries are hidden by default;
- all raw technical outputs remain available through the global **Technical details** switch;
- the backup button is disabled until the repository is ready;
- an AST regression guard rejects unprotected technical output;
- Step 151.2 repository, line-ending and UI runtime guarantees remain active.

## Final operator verification

```powershell
git push origin main
python .\\scripts\\verify_step_151_2_1.py --require-synced
python .\\tools\\finalize_step_151_2_1_release.py --verify-only
git status -sb
```

Accepted final status: `## main...origin/main` with no additional lines.
""",
        encoding="utf-8",
        newline="\n",
    )

    return {
        "ok": True,
        "checkpoint": CHECKPOINT,
        "release_manifest_entries": len(rows),
        "release_manifest_sha256": release_sha,
        "removed_legacy_metadata": removed,
        "repository": repository,
        "backup_ui": backup_ui,
    }


def verify_manifests() -> dict:
    release = _load_json(RELEASE_MANIFEST)
    result = validate_release_manifest(release, root=ROOT, expected_checkpoint=CHECKPOINT)
    failures = list(result.get("failures", []))
    for path in METADATA_FILES:
        if not path.is_file():
            failures.append(f"missing_metadata:{path.name}")
    listed = {str(row.get("path")) for row in release.get("files", []) if isinstance(row, dict)}
    if "data/user_journal.db" in listed:
        failures.append("personal_journal_in_release_manifest")
    if any(path.startswith("data/user_journal_exports/") for path in listed):
        failures.append("personal_exports_in_release_manifest")
    result.update(ok=not failures, failure_count=len(failures), failures=failures)
    return result


def default_archive_path() -> Path:
    stamp = datetime.now(ZoneInfo("Europe/Sofia")).strftime("%Y%m%d_%H%M%S")
    return ROOT.parent / f"lottery-probability-model_STEP151_2_1_USER-BACKUP-UI_TECHNICAL-SEPARATION_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize Step 151.2.1 release metadata")
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
    if result.get("ok") and args.build_zip:
        destination = (args.output or default_archive_path()).resolve()
        result["clean_zip"] = build_clean_zip(destination, root=ROOT, metadata_files=METADATA_FILES)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
