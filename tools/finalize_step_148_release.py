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
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP148.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP148.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 148"
CHECKPOINT_TITLE = "Prospective Forward-Test Lock & Untouched Future Draw Ledger"
BASE_COMMIT = "278892b"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def write_manifests() -> dict:
    for legacy in (
        ROOT / "CLEAN_ZIP_MANIFEST_STEP147.md",
        ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP147.md",
    ):
        legacy.unlink(missing_ok=True)

    rows = collect_release_rows(root=ROOT)
    status = load_json(ROOT / "models/v148_prospective_forward_test_status.json")
    summary = load_json(ROOT / "reports/v148_forward_test_summary.json")
    release = {
        "checkpoint": CHECKPOINT,
        "checkpoint_title": CHECKPOINT_TITLE,
        "project": "lottery-probability-model",
        "release_policy_version": POLICY_VERSION,
        "manifest_scope": release_scope_description(),
        "runtime_artifact_policy": {
            "runtime_root": "reports/runtime/v145_1_artifact_integrity/",
            "tracked_snapshots_update_only_on_semantic_change": True,
            "runtime_cache_in_release": False,
        },
        "prospective_forward_test_scope": {
            "protocol_id": status.get("protocol_id"),
            "target_settled_draws": status.get("target_settled_draws"),
            "eligible_settled_draws": status.get("eligible_settled_draws"),
            "active_expected_draw_key": status.get("active_expected_draw_key"),
            "append_only_sha256_ledger": True,
            "score_before_learn": True,
            "historical_backfill": False,
            "frozen_step146_configuration": True,
            "production_promotion": "blocked",
            "automatic_production_promotion": False,
        },
        "forbidden_release_classes": [
            ".git and local environments",
            "runtime caches and local audit output",
            "Python, test and Jupyter caches",
            "secret environment files",
            "temporary archives, logs and backups",
            "build output and editor metadata",
        ],
        "file_count": len(rows),
        "files": rows,
    }
    write_json_atomic(RELEASE_MANIFEST, release)
    release_sha = sha256_file(RELEASE_MANIFEST)
    project_count = len(rows) + len(METADATA_FILES)

    clean = f"""# CLEAN ZIP MANIFEST — STEP 148

- Project: `lottery-probability-model`
- Checkpoint: `Step 148 — {CHECKPOINT_TITLE}`
- Base code checkpoint: `Step 147`, commit `{BASE_COMMIT}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Verification chain: `STEP_122_VERIFY_OK` through `STEP_147_VERIFY_OK`
- Step 148 verification: `STEP_148_VERIFY_OK`
- Protocol ID: `{status.get('protocol_id', 'unknown')}`
- Active expected draw: `{status.get('active_expected_draw_key', 'unknown')}`
- Eligible settled draws: **{status.get('eligible_settled_draws', 'unknown')} / {status.get('target_settled_draws', 'unknown')}**
- Ledger integrity: **{'PASS' if status.get('ledger_integrity_ok') else 'FAIL'}**
- Production promotion approved: **No**
- Automatic production promotion: **No**
- Production integration enabled: **No**
- Real ticket generation enabled: **No**
- Personal journal modified by Step 148: **No**
- Historical backfill performed: **No**
- Runtime cache included in archive: **No**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**
- Bundled `.pyc` / `.zip` / `.log` / backup artifacts: **No**

## Step 148 result

- A 30-draw prospective evaluation protocol is initialized.
- Milestones are fixed at 10, 20 and 30 eligible future draws.
- The Step 146 algorithm, parameters and seeds are frozen.
- The initial pre-draw forecast is locked for `{status.get('active_expected_draw_key', 'the next unseen draw')}`.
- Ledger events are chained with canonical SHA-256 hashes.
- Draws without a valid pre-draw lock are excluded and never backfilled.
- Step 147 production blocking remains in force.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = rf"""# Full CLEAN Checkpoint Manifest — Step 148

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 148 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{BASE_COMMIT}` (`Step 147`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Scope

- Starts an untouched prospective forward-test window after Step 147.
- Freezes the Step 146 algorithm, configuration and random seeds.
- Commits evaluation packages before the next draw enters the canonical dataset.
- Uses an append-only SHA-256 event chain and immutable lock artifacts.
- Enforces score-before-learn chronology.
- Excludes draws without a valid pre-draw lock instead of backfilling them.
- Tracks milestones after 10, 20 and 30 eligible future draws.
- Preserves the Step 147 production block and requires a new decision after 30 draws.
- Does not access the personal journal or production ticket pipeline.

## Initial protocol state

- Protocol ID: `{status.get('protocol_id', 'unknown')}`
- Status: `{status.get('status', 'unknown')}`
- Ledger events: `{status.get('ledger_event_count', 'unknown')}`
- Active lock: `{status.get('active_lock_id', 'unknown')}`
- Expected draw: `{status.get('active_expected_draw_key', 'unknown')}`
- Eligible settled draws: `{status.get('eligible_settled_draws', 'unknown')}`
- Remaining draws: `{status.get('remaining_draws', 'unknown')}`
- Result signature: `{status.get('result_signature_sha256', 'unknown')}`

## Verification

- Previous verifier chain through Step 147: **PASS required**
- Step 148 ledger chain integrity: **PASS required**
- Frozen source signature validation: **PASS required**
- Deterministic active-lock reproduction: **PASS required**
- No historical backfill: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Personal journal modified: **No**

## Local checks

```powershell
python .\scripts\verify_step_147.py
python .\scripts\verify_step_148.py
python .\tools\finalize_step_148_release.py --verify-only
python .\tools\finalize_step_148_release.py --build-zip

git status -sb
```

The generated archive is validated independently after creation. Its SHA-256 is printed by the finalizer and is intentionally not embedded into a file contained inside the same archive.
"""
    FULL_MANIFEST.write_text(full, encoding="utf-8")
    return {
        "ok": True,
        "checkpoint": CHECKPOINT,
        "project_file_count": project_count,
        "release_manifest_entries": len(rows),
        "release_manifest_sha256": release_sha,
        "release_policy_version": POLICY_VERSION,
        "protocol_id": status.get("protocol_id"),
        "active_expected_draw_key": status.get("active_expected_draw_key"),
        "result_signature_sha256": summary.get("result_signature_sha256"),
    }


def verify_manifests() -> dict:
    release = load_json(RELEASE_MANIFEST)
    result = validate_release_manifest(release, root=ROOT, expected_checkpoint=CHECKPOINT)
    failures = list(result.get("failures", []))
    for path in (CLEAN_MANIFEST, FULL_MANIFEST):
        if not path.is_file():
            failures.append(f"missing_metadata:{path.name}")
    result.update(ok=not failures, failure_count=len(failures), failures=failures)
    return result


def default_archive_path() -> Path:
    stamp = datetime.now(ZoneInfo("Europe/Sofia")).strftime("%Y%m%d_%H%M%S")
    return ROOT.parent / f"lottery-probability-model_STEP148_PROSPECTIVE-FORWARD-TEST-LOCK_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 148 release metadata")
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
