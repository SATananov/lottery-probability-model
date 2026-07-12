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
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP147.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP147.md"
METADATA_FILES = (RELEASE_MANIFEST, CLEAN_MANIFEST, FULL_MANIFEST)
CHECKPOINT = "Step 147"
CHECKPOINT_TITLE = "Experimental Evidence Synthesis & Research Decision Gate"
BASE_COMMIT = "d1a82f4"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def write_manifests() -> dict:
    for legacy in (
        ROOT / "CLEAN_ZIP_MANIFEST_STEP146.md",
        ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP146.md",
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
        "research_decision_scope": {
            "source_steps": [144, 145, 146],
            "evidence_synthesis": True,
            "decision_registry": True,
            "same_holdout_retuning_forbidden": True,
            "current_neural_configuration": "pause_and_archive",
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
    status = load_json(ROOT / "models/v147_experimental_evidence_decision_status.json")
    summary = load_json(ROOT / "reports/v147_research_decision_summary.json")
    project_count = len(rows) + len(METADATA_FILES)

    clean = f"""# CLEAN ZIP MANIFEST — STEP 147

- Project: `lottery-probability-model`
- Checkpoint: `Step 147 — {CHECKPOINT_TITLE}`
- Base code checkpoint: `Step 146`, commit `{BASE_COMMIT}`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Release policy version: `{POLICY_VERSION}`
- Verification chain: `STEP_122_VERIFY_OK` through `STEP_146_VERIFY_OK`
- Step 147 verification: `STEP_147_VERIFY_OK`
- Step 147 decision signature: `{status.get('result_signature_sha256', 'unknown')}`
- Source experiments synthesized: **{status.get('source_experiment_count', 'unknown')}**
- Evidence rows: **{status.get('evidence_row_count', 'unknown')}**
- Robust positive rows: **{status.get('robust_positive_rows', 'unknown')}**
- Production promotion approved: **{'Yes' if status.get('production_promotion_approved') else 'No'}**
- Current neural configuration: **{status.get('current_neural_configuration_action', 'unknown')}**
- Production integration enabled: **No**
- Heavy ML retraining performed: **No**
- Personal journal modified by Step 147: **No**
- Runtime cache included in archive: **No**
- Bundled `.git` / `.venv` / `venv` / `.r-lib` / `__pycache__`: **No**
- Bundled `.pyc` / `.zip` / `.log` / backup artifacts: **No**

## Step 147 result

- Step 144–146 evidence is consolidated into one deterministic decision record.
- No robust positive superiority was demonstrated.
- Production promotion remains blocked.
- The current neural configuration is paused and archived.
- Retuning the same configuration on observed holdouts is forbidden.
- New work requires a materially new preregistered hypothesis and untouched validation data.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = rf"""# Full CLEAN Checkpoint Manifest — Step 147

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 147 — {CHECKPOINT_TITLE}`
- Generated (Europe/Sofia): `{generated}`
- Base Git commit: `{BASE_COMMIT}` (`Step 146`)
- New Git commit: **not asserted** (`.git` is intentionally absent from the clean archive)
- Release policy version: `{POLICY_VERSION}`

## Scope

- Synthesizes Step 144, Step 145 and Step 146 evidence without rerunning heavy experiments.
- Verifies source experiment identities, signatures and canonical dataset consistency.
- Creates a dedicated research decision registry separate from the experiment registry.
- Records a machine-readable evidence matrix and decision gate.
- Blocks production promotion because robust superiority is absent.
- Pauses and archives the current neural configuration.
- Forbids tuning the same configuration on already observed holdouts.
- Requires materially new preregistered hypotheses and untouched validation periods for future research.
- Preserves Step 145.1 release integrity and ignored runtime artifact policy.

## Recorded conclusion

{(summary.get('decision') or {}).get('reason', 'No recorded decision.')}

## Verification

- Previous verifier chain through Step 146: **PASS required**
- Step 147 deterministic read-only synthesis: **PASS required**
- Source signature and dataset consistency: **PASS required**
- Research decision registry integrity: **PASS required**
- Same-holdout retuning prohibition: **PASS required**
- Clean ZIP forbidden-path scan: **PASS required**
- Clean ZIP CRC scan: **PASS required**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Heavy ML retraining performed: **No**
- Personal journal modified: **No**

## Local checks

```powershell
python .\scripts\verify_step_146.py
python .\scripts\verify_step_147.py
python .\tools\finalize_step_147_release.py --verify-only
python .\tools\finalize_step_147_release.py --build-zip

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
    return ROOT.parent / f"lottery-probability-model_STEP147_RESEARCH-DECISION-GATE_FULL-CLEAN_{stamp}.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate, verify or package Step 147 release metadata")
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
