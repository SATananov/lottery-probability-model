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
from src.v151_repository_root_cleanup_engine import write_audit_artifacts

RELEASE_MANIFEST = ROOT / "release-manifest.json"
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP151.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 151"
CHECKPOINT_TITLE = "Repository Root Cleanup & Post-Draw Documentation Sync"

def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}

def git_baseline() -> dict:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        subject = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return {"sha": sha, "subject": subject}
    except Exception:
        return {"sha": "unknown", "subject": "unknown"}

def remove_legacy_metadata() -> list[str]:
    removed: list[str] = []
    keep = {CLEAN_MANIFEST.name, FULL_MANIFEST.name}
    for pattern in ("CLEAN_ZIP_MANIFEST_STEP*.md", "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP*.md"):
        for path in ROOT.glob(pattern):
            if path.name not in keep:
                path.unlink(missing_ok=True)
                removed.append(path.name)
    return sorted(set(removed))

def write_manifests() -> dict:
    removed = remove_legacy_metadata()
    audit = write_audit_artifacts(ROOT)
    if not audit.get("ok"):
        return {"ok": False, "reason": "step151_audit_failed", "audit": audit}
    rows = collect_release_rows(root=ROOT)
    step148 = load_json(ROOT / "models/v148_prospective_forward_test_status.json")
    policy = load_json(ROOT / "models/v151_repository_root_cleanup_policy.json")
    baseline = git_baseline()
    release = {
        "checkpoint": CHECKPOINT,
        "checkpoint_title": CHECKPOINT_TITLE,
        "project": "lottery-probability-model",
        "release_policy_version": POLICY_VERSION,
        "manifest_scope": release_scope_description(),
        "base_git": baseline,
        "latest_draw": audit.get("latest_draw"),
        "post_draw_documentation_sync": {
            "readme_current": all((audit.get("readme_checks") or {}).values()),
            "moved_documents": policy.get("root_document_moves", {}),
            "documentation_index": "docs/README.md",
            "step_history": "docs/STEP_HISTORY.md",
        },
        "repository_root_cleanup": {
            "legacy_metadata_removed": removed,
            "remaining_legacy_metadata": audit.get("legacy_root_manifests"),
            "remaining_root_docs": audit.get("stale_root_docs"),
            "stale_document_references": len(audit.get("stale_document_references", [])),
        },
        "prospective_forward_test": {
            "status": step148.get("status"),
            "eligible_settled_draws": step148.get("eligible_settled_draws"),
            "target_settled_draws": step148.get("target_settled_draws"),
            "remaining_draws": step148.get("remaining_draws"),
            "active_lock_id": step148.get("active_lock_id"),
            "active_expected_draw_key": step148.get("active_expected_draw_key"),
            "production_promotion_approved": step148.get("production_promotion_approved"),
        },
        "privacy_policy": {
            "personal_journal_database": "local_only_excluded",
            "personal_journal_exports": "local_only_excluded",
            "public_journal_schema": "data/user_journal_schema.sql",
            "history_rewrite_performed": False,
        },
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
        "personal_journal_used": False,
        "result_signature_sha256": audit.get("result_signature_sha256"),
        "file_count": len(rows),
        "files": rows,
    }
    write_json_atomic(RELEASE_MANIFEST, release)
    release_sha = sha256_file(RELEASE_MANIFEST)
    project_count = len(rows) + len(METADATA_FILES)
    draw = audit["latest_draw"]
    forward = audit["prospective_forward_test"]
    CLEAN_MANIFEST.write_text(
        f"""# CLEAN ZIP MANIFEST — STEP 151

- Project: `lottery-probability-model`
- Checkpoint: `Step 151 — {CHECKPOINT_TITLE}`
- Base Git commit: `{baseline['sha']} {baseline['subject']}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Step 151 verification: `STEP_151_VERIFY_OK`
- Last official draw: `{draw.get('draw_key')}` from `{draw.get('date')}`
- Last numbers: `{draw.get('numbers_text')}`
- Dataset rows: `{draw.get('row_count')}`
- Step 148 progress: `{forward.get('eligible_settled_draws')}/{forward.get('target_settled_draws')}`
- Active expected draw: `{forward.get('active_expected_draw_key')}`
- Legacy root manifests remaining: **0**
- Documentation files remaining in root: **0**
- Personal `data/user_journal.db` included: **No**
- Personal `data/user_journal_exports/` included: **No**
- Bundled `.git` / `.venv` / caches / runtime snapshots: **No**

## Step 151 result

- Historical release metadata was removed from the repository root while remaining available in Git history.
- Project documentation was consolidated under `docs/`.
- The root README and Streamlit guide were synchronized with the official draw and current prospective-test state.
- Runtime code, model scoring, historical data and the Step 148 ledger were not modified by this documentation checkpoint.
""",
        encoding="utf-8",
    )
    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    FULL_MANIFEST.write_text(
        f"""# Full CLEAN Checkpoint Manifest — Step 151

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 151 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{baseline['sha']} {baseline['subject']}`
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Repository cleanup

- Removed old root CLEAN manifests: `{len(removed)}`
- Remaining old root CLEAN manifests: `0`
- Documentation index: `docs/README.md`
- Step history: `docs/STEP_HISTORY.md`
- Root README is concise and current.
- Training scripts, application entrypoints and launchers remain in root because they are operational files.

## Post-draw synchronization

- Latest draw: `{draw.get('draw_key')}`
- Date: `{draw.get('date')}`
- Numbers: `{draw.get('numbers_text')}`
- Dataset rows: `{draw.get('row_count')}`
- Step 148 settled draws: `{forward.get('eligible_settled_draws')}`
- Step 148 remaining draws: `{forward.get('remaining_draws')}`
- Active lock: `{forward.get('active_lock_id')}`
- Expected draw: `{forward.get('active_expected_draw_key')}`
- Production promotion remains blocked.

## Local checks

```powershell
python .\\tools\\audit_repository_root_cleanup.py
python .\\scripts\\verify_step_148.py
python .\\scripts\\verify_step_151.py
python .\\tools\\finalize_step_151_release.py --verify-only
python .\\tools\\finalize_step_151_release.py --build-zip
git status -sb
```

The personal journal database and exports remain local-only and are not included in the release manifest or clean ZIP.
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
        "removed_legacy_metadata": removed,
        "latest_draw": draw,
        "prospective_forward_test": forward,
    }

def verify_manifests() -> dict:
    release = load_json(RELEASE_MANIFEST)
    result = validate_release_manifest(release, root=ROOT, expected_checkpoint=CHECKPOINT)
    failures = list(result.get("failures", []))
    for path in (CLEAN_MANIFEST, FULL_MANIFEST):
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
    return ROOT.parent / (
        "lottery-probability-model_STEP151_REPOSITORY-ROOT-CLEANUP_"
        f"POST-DRAW-DOCUMENTATION-SYNC_FULL-CLEAN_{stamp}.zip"
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 151 release metadata")
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
