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
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP146.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP146.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 146"
CHECKPOINT_TITLE = "Controlled Neural Experiment Expansion & Robustness Validation"
BASE_COMMIT = "b1c02a1"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def write_manifests() -> dict:
    for legacy in (
        ROOT / "CLEAN_ZIP_MANIFEST_STEP145_1.md",
        ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP145_1.md",
    ):
        legacy.unlink(missing_ok=True)

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
            "runtime_cache_in_release": False,
        },
        "experimental_scope": {
            "step": 146,
            "research_only": True,
            "multi_seed": True,
            "non_overlapping_historical_folds": True,
            "confidence_intervals": True,
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
    status = load_json(ROOT / "models/v146_controlled_neural_robustness_status.json")
    summary = load_json(ROOT / "reports/v146_neural_robustness_summary.json")
    comparison = summary.get("comparison", {}) or {}
    project_count = len(rows) + len(METADATA_FILES)

    clean = f"""# CLEAN ZIP MANIFEST — STEP 146

- Project: `lottery-probability-model`
- Checkpoint: `Step 146 — {CHECKPOINT_TITLE}`
- Base code checkpoint: `Step 145.1`, commit `{BASE_COMMIT}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Verification chain: `STEP_122_VERIFY_OK` through `STEP_145_1_VERIFY_OK`
- Step 146 verification: `STEP_146_VERIFY_OK`
- Step 146 result signature: `{status.get('result_signature_sha256', 'unknown')}`
- Robustness runs: **{status.get('run_count', 'unknown')}**
- Promotion gate passed: **{'Yes' if comparison.get('promotion_gate_passed') else 'No'}**
- Production integration enabled: **No**
- Heavy ML retraining performed: **No**
- Personal journal modified by Step 146: **No**
- Runtime cache included in archive: **No**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**
- Bundled `.pyc` / `.zip` / `.log` / backup artifacts: **No**

## Step 146 result

- Three non-overlapping historical walk-forward folds.
- Five deterministic neural seeds.
- Fifteen seed/fold robustness runs.
- 95% bootstrap confidence intervals and exact sign tests.
- Additional recent-window and frequency–recency blend baselines.
- Promotion remains blocked because robust superiority was not demonstrated.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = rf"""# Full CLEAN Checkpoint Manifest — Step 146

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 146 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{BASE_COMMIT}` (`Step 145.1`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Scope

- Adds controlled multi-seed neural robustness validation.
- Uses three non-overlapping chronological holdout folds of 120 draws each.
- Uses five deterministic seeds and fifteen complete walk-forward runs.
- Compares neural dynamics with frequency, recency, recent-window frequency, frequency–recency blend and uniform-random mean baselines.
- Records deterministic 95% bootstrap confidence intervals, exact sign tests and stability rates by seed and fold.
- Preserves strict score-before-learn chronology for every target draw.
- Keeps neural experiments isolated from production ticket generation.
- Preserves Step 145.1 clean release and ignored runtime artifact policy.

## Recorded conclusion

The neural configuration is reasonably stable across seeds, but does not demonstrate robust superiority. The default Step 146 promotion gate is **BLOCKED**. This negative result is retained as valid experimental evidence.

## Verification

- Previous verifier chain through Step 145.1: **PASS required**
- Step 146 deterministic read-only reproduction: **PASS required**
- Step 146 multi-seed and multi-fold structure: **PASS required**
- Step 146 confidence and stability artifacts: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Heavy ML retraining performed: **No**
- Personal journal modified: **No**

## Local checks

```powershell
python .\scripts\verify_step_145_1.py
python .\scripts\verify_step_146.py
python .\tools\finalize_step_146_release.py --verify-only
python .\tools\finalize_step_146_release.py --build-zip

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
    return ROOT.parent / f"lottery-probability-model_STEP146_NEURAL-ROBUSTNESS-VALIDATION_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 146 release metadata")
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
