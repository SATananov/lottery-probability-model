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
from src.v151_5_post_sync_integrity_cleanup_engine import (
    CHECKPOINT,
    CHECKPOINT_TITLE,
    REPORT_PATH,
    audit_post_sync_state,
    prepare_checkpoint,
    write_artifacts,
)

RELEASE_MANIFEST = ROOT / "release-manifest.json"
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP151_5.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151_5.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()
    except Exception:
        return "unknown"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def _remove_old_manifests() -> list[str]:
    keep = {CLEAN_MANIFEST.name, FULL_MANIFEST.name}
    removed: list[str] = []
    for pattern in ("CLEAN_ZIP_MANIFEST_STEP*.md", "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP*.md"):
        for path in ROOT.glob(pattern):
            if path.name not in keep:
                path.unlink(missing_ok=True)
                removed.append(path.name)
    return sorted(set(removed))


def _update_docs() -> None:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8-sig")
    marker = "Repository checkpoint: **Step 151.2.2**"
    replacement = (
        "Repository checkpoint: **Step 151.5** — Prize History and all downstream layers are synchronized "
        "through official draw `2026-55`; Step 148 has two settled prospective draws and an immutable active "
        "lock for `2026-56`; transient runtime snapshots are excluded from the checkpoint."
    )
    if marker in text:
        start = text.index(marker)
        end = text.find("\n", start)
        if end < 0:
            end = len(text)
        text = text[:start] + replacement + text[end:]
    elif "Repository checkpoint: **Step 151.5**" not in text:
        text = text.rstrip() + "\n\n" + replacement + "\n"
    readme.write_text(text, encoding="utf-8", newline="\n")

    history = ROOT / "docs/STEP_HISTORY.md"
    history_text = history.read_text(encoding="utf-8-sig")
    if "## Step 151.5 — Full Post-Synchronization Integrity Audit" not in history_text:
        history_text = history_text.rstrip() + """

## Step 151.3 — Prize History Integrity, CAPTCHA Diagnostics and Freshness Repair

Step 151.3 repairs the Prize History persistence boundary so an empty SQLite table cannot erase a non-empty canonical CSV. Manual import now validates unique sorted numbers, date/year consistency, official source URLs and contiguous draw order. The BST detector distinguishes an index CAPTCHA from a parser-format failure, Step 120 compares exact latest-draw equality and Step 131 counts every blocking freshness state.

## Step 151.4 — Controlled Prize History 54–55 Data Synchronization and Step 148 Settlement

Step 151.4 imports the verified official Prize History records for draws 54 and 55, synchronizes historical, normalized and canonical datasets through `2026-55`, refreshes the R and lightweight downstream layers without heavy retraining, closes Step 143.3 with zero blockers, settles the frozen Step 148 package for draw 55 and creates the next immutable lock for `2026-56`.

## Step 151.5 — Full Post-Synchronization Integrity Audit, Runtime Cleanup and Clean Git Checkpoint

Step 151.5 verifies 32 Prize History rows, 10065 synchronized dataset rows, zero freshness blockers, R coverage through draw 55, an intact Step 148 ledger with two settlements and an active lock for draw 56. Transient BST/startup/operations runtime snapshots are restored to the previous committed baseline, disposable caches are removed, heavy model hashes are verified unchanged and the repository is prepared for an explicit clean commit and push.
"""
    history.write_text(history_text, encoding="utf-8", newline="\n")


def _write_report() -> None:
    REPORT_PATH.write_text(
        "# Step 151.5 — Full Post-Synchronization Integrity Audit, Runtime Cleanup and Clean Git Checkpoint\n\n"
        "## Closed state\n\n"
        "- Prize History contains 32 official records through draw 2026-55.\n"
        "- Historical, normalized and canonical datasets contain 10065 rows and agree on draw 2026-55.\n"
        "- Step 120 is MODEL_DATA_SYNCED and Step 122 has zero blockers.\n"
        "- The R statistical layer is refreshed through draw 55.\n"
        "- Step 143.3 is completed.\n"
        "- Step 148 has two settled prospective draws and an active immutable lock for 2026-56.\n"
        "- Heavy model artifacts are unchanged and no heavy retraining was performed.\n"
        "- Transient runtime snapshots are not promoted into the clean checkpoint.\n"
        "- Local journal data and exports remain excluded from Git and clean ZIP packages.\n\n"
        "Commit and push remain explicit operator actions.\n",
        encoding="utf-8", newline="\n",
    )


def write_release_metadata() -> dict:
    removed = _remove_old_manifests()
    _update_docs()
    _write_report()
    audit = audit_post_sync_state(allow_volatile=False)
    if not audit.get("ok"):
        return {"ok": False, "reason": "post_sync_audit_failed", "audit": audit}
    write_artifacts(audit)
    rows = collect_release_rows(root=ROOT)
    step148 = _load(ROOT / "models/v148_prospective_forward_test_status.json")
    release = {
        "checkpoint": CHECKPOINT,
        "checkpoint_title": CHECKPOINT_TITLE,
        "project": "lottery-probability-model",
        "release_policy_version": POLICY_VERSION,
        "manifest_scope": release_scope_description(),
        "parent_git": {"sha": _git("rev-parse", "--short", "HEAD"), "subject": _git("log", "-1", "--pretty=%s", "HEAD")},
        "repository_sync": audit.get("git"),
        "line_endings": audit.get("line_endings"),
        "post_sync_integrity": audit,
        "fresh_clone_verification_command": "python scripts/verify_step_151_5.py --require-synced",
        "external_github_push_asserted": False,
        "prospective_forward_test": {
            "status": step148.get("status"),
            "eligible_settled_draws": step148.get("eligible_settled_draws"),
            "target_settled_draws": step148.get("target_settled_draws"),
            "active_lock_id": step148.get("active_lock_id"),
            "active_expected_draw_key": step148.get("active_expected_draw_key"),
            "production_promotion_approved": step148.get("production_promotion_approved"),
        },
        "privacy_policy": {"personal_journal_database": "local_only_excluded", "personal_journal_exports": "local_only_excluded"},
        "legacy_release_metadata_removed": removed,
        "historical_draw_data_changed": True,
        "synchronized_through_draw": "2026-55",
        "heavy_model_retraining_performed": False,
        "production_scoring_changed": False,
        "personal_journal_used_for_modeling": False,
        "file_count": len(rows),
        "files": rows,
    }
    write_json_atomic(RELEASE_MANIFEST, release)
    release_sha = sha256_file(RELEASE_MANIFEST)
    git = audit["git"]
    CLEAN_MANIFEST.write_text(
        f"# CLEAN ZIP MANIFEST — STEP 151.5\n\n"
        f"- Project: `lottery-probability-model`\n"
        f"- Checkpoint: `{CHECKPOINT} — {CHECKPOINT_TITLE}`\n"
        f"- Parent Git commit: `{release['parent_git']['sha']} {release['parent_git']['subject']}`\n"
        f"- Release manifest entries: **{len(rows)}**\n"
        f"- Release manifest SHA-256: `{release_sha}`\n"
        f"- Synchronized through draw: `2026-55`\n"
        f"- Step 148 active expected draw: `{step148.get('active_expected_draw_key')}`\n"
        f"- Heavy model retraining: **No**\n"
        f"- Local branch: `{git.get('branch')}`\n"
        f"- Ahead / behind before commit: `{git.get('ahead')}` / `{git.get('behind')}`\n"
        "- Personal journal database included: **No**\n"
        "- Personal journal exports included: **No**\n"
        "- Bundled `.git`, `.venv`, caches, logs and backups: **No**\n\n"
        "Final acceptance requires commit, push and `python scripts/verify_step_151_5.py --require-synced`.\n",
        encoding="utf-8", newline="\n",
    )
    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    FULL_MANIFEST.write_text(
        f"# Full CLEAN Checkpoint Manifest — Step 151.5\n\n"
        f"- Generated: `{generated}`\n"
        f"- Parent Git: `{release['parent_git']['sha']} {release['parent_git']['subject']}`\n"
        "- Prize History rows: `32`\n"
        "- Historical / normalized / canonical rows: `10065`\n"
        "- Latest synchronized draw: `2026-55` — `5, 10, 17, 20, 42, 47`\n"
        "- Freshness blockers: `0`\n"
        "- Step 148 settled draws: `2 / 30`\n"
        f"- Active lock: `{step148.get('active_lock_id')}` for `{step148.get('active_expected_draw_key')}`\n"
        "- Heavy models unchanged: `Yes`\n"
        "- Production promotion: `Blocked`\n"
        "- Local journal and exports: `Excluded`\n\n"
        "Final verification:\n\n"
        "```powershell\n"
        "python .\\scripts\\verify_step_151_5.py --require-synced\n"
        "git status -sb\n"
        "```\n\n"
        "Accepted Git status: `## main...origin/main` with no additional lines.\n",
        encoding="utf-8", newline="\n",
    )
    # Metadata changed release scope; regenerate once so all docs/reports are represented.
    rows = collect_release_rows(root=ROOT)
    release["file_count"] = len(rows)
    release["files"] = rows
    write_json_atomic(RELEASE_MANIFEST, release)
    return {"ok": True, "release_manifest_entries": len(rows), "release_manifest_sha256": sha256_file(RELEASE_MANIFEST), "removed_legacy_metadata": removed, "audit": audit}


def verify_release_metadata() -> dict:
    release = _load(RELEASE_MANIFEST)
    result = validate_release_manifest(release, root=ROOT, expected_checkpoint=CHECKPOINT)
    missing = [str(path.relative_to(ROOT)) for path in METADATA_FILES if not path.is_file()]
    failures = list(result.get("failures", [])) + [f"missing_metadata:{item}" for item in missing]
    result.update(ok=not failures, failures=failures, failure_count=len(failures))
    return result


def default_archive_path() -> Path:
    stamp = datetime.now(ZoneInfo("Europe/Sofia")).strftime("%Y%m%d_%H%M%S")
    return ROOT.parent / f"lottery-probability-model_STEP151_5_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--build-zip", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare:
        result = prepare_checkpoint()
        if result.get("ok"):
            result["release"] = write_release_metadata()
            result["verification"] = verify_release_metadata()
            result["ok"] = bool(result.get("release", {}).get("ok")) and bool(result.get("verification", {}).get("ok"))
    else:
        result = verify_release_metadata()
    if result.get("ok") and args.build_zip:
        destination = (args.output or default_archive_path()).resolve()
        result["clean_zip"] = build_clean_zip(destination, root=ROOT, metadata_files=METADATA_FILES)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
