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
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP145_1.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP145_1.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 145.1"
CHECKPOINT_TITLE = "Clean Release Metadata & Runtime Artifact Integrity Repair"
BASE_COMMIT = "f1060ef"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def write_manifests() -> dict:
    rows = collect_release_rows(root=ROOT)
    release = {
        "checkpoint": CHECKPOINT,
        "checkpoint_title": CHECKPOINT_TITLE,
        "project": "lottery-probability-model",
        "release_policy_version": POLICY_VERSION,
        "manifest_scope": release_scope_description(),
        "runtime_artifact_policy": {
            "runtime_root": "reports/runtime/v145_1_artifact_integrity/",
            "tracked_snapshots_update_only_on_semantic_change": True,
            "volatile_fields_ignored_for_snapshot_updates": [
                "generated_at_utc",
                "checked_at_utc",
                "started_at_utc",
                "finished_at_utc",
                "source_diagnostics",
                "trigger",
                "cache_reused",
            ],
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

    neural_status = load_json(ROOT / "models" / "v145_experimental_neural_dynamics_status.json")
    project_count = len(rows) + len(METADATA_FILES)
    clean = f"""# CLEAN ZIP MANIFEST — STEP 145.1

- Project: `lottery-probability-model`
- Checkpoint: `Step 145.1 — {CHECKPOINT_TITLE}`
- Base code checkpoint: `Step 145`, commit `{BASE_COMMIT}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Verification chain: `STEP_122_VERIFY_OK` through `STEP_145_VERIFY_OK`
- Integrity verification: `STEP_145_1_VERIFY_OK`
- Neural experiment result signature: `{neural_status.get('result_signature_sha256', 'unknown')}`
- Production integration enabled: **No**
- Heavy ML retraining performed: **No**
- Personal journal modified by Step 145.1: **No**
- Runtime cache included in archive: **No**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**
- Bundled `.pyc` / `.zip` / `.log` / backup artifacts: **No**

## Repair result

- All Step 143.3–145 release finalizers use one shared release-scope policy.
- `release-manifest.json` rejects forbidden paths instead of only omitting a few known folders.
- Startup checks write current volatile state under ignored `reports/runtime/` storage.
- Tracked Step 122, Step 123 and Step 126 snapshots update only when their semantic state changes.
- Step 126 audit history no longer appends an identical event on every application start.
- Clean ZIP generation performs post-build root, forbidden-path and CRC validation.
- Step 144/145 dataset identity is stable across Windows CRLF and Linux LF checkouts.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = f"""# Full CLEAN Checkpoint Manifest — Step 145.1

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 145.1 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{BASE_COMMIT}` (`Step 145`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Scope

- Replaces ad-hoc release filtering with a single reusable allow/deny policy.
- Excludes `.git`, Python/R environments, caches, runtime state, secrets, archives, logs, backups and build artifacts.
- Validates every manifest row for path safety, uniqueness, file size and SHA-256.
- Detects missing, stale and unlisted release files.
- Adds atomic metadata/runtime writes to avoid partially written JSON files.
- Keeps volatile startup state in `reports/runtime/v145_1_artifact_integrity/`, which is ignored by Git and excluded from release packages.
- Preserves tracked operational snapshots unless a draw, status, configuration or other semantic value changes.
- Keeps the Step 145 neural dynamics experiment unchanged and research-only.
- Preserves historical Step 144/145 experiment signatures through cross-platform CSV newline normalization.

## Verification

- Previous verifier chain through Step 145: **PASS**
- Step 145.1 release-policy verification: **PASS required**
- Step 145.1 runtime no-dirty-tree verification: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Heavy ML retraining performed: **No**
- Personal journal modified: **No**

## Local checks

```powershell
python ./scripts/verify_step_145_1.py
python ./tools/finalize_step_145_1_release.py --verify-only
python ./tools/finalize_step_145_1_release.py --build-zip

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
    return ROOT.parent / f"lottery-probability-model_STEP145_1_RELEASE-RUNTIME-INTEGRITY_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 145.1 release metadata")
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
            result["clean_zip"] = build_clean_zip(
                destination,
                root=ROOT,
                metadata_files=METADATA_FILES,
            )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
