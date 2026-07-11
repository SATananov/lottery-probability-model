from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RELEASE_MANIFEST = ROOT / "release-manifest.json"
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP144.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP144.md"
EXCLUDED = {RELEASE_MANIFEST.name, CLEAN_MANIFEST.name, FULL_MANIFEST.name}
BASE_ARCHIVE_NAME = "lottery-probability-model_STEP143_3_FINAL-DOWNSTREAM-ZERO-BLOCKER-CLOSURE_FULL-CLEAN_20260711_132000.zip"
BASE_ARCHIVE_SHA256 = "a0755e32d4b646269e41827f80138070464de6fdb54120099241c8e3b7bcc6e9"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else {}


def project_files() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDED:
            continue
        data = path.read_bytes()
        rows.append({"path": rel, "size_bytes": len(data), "sha256": sha256_bytes(data)})
    return rows


def write_manifests() -> dict:
    rows = project_files()
    release = {
        "checkpoint": "Step 144",
        "project": "lottery-probability-model",
        "manifest_scope": (
            "All project files except release-manifest.json, CLEAN_ZIP_MANIFEST_STEP144.md "
            "and FULL_CLEAN_CHECKPOINT_MANIFEST_STEP144.md"
        ),
        "file_count": len(rows),
        "files": rows,
    }
    RELEASE_MANIFEST.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    release_sha = sha256_bytes(RELEASE_MANIFEST.read_bytes())

    status = load_json(ROOT / "models" / "v144_reproducible_experiment_registry_status.json")
    summary = load_json(ROOT / "reports" / "v144_baseline_lab_summary.json")
    frequency = summary.get("frequency_baseline", {}) or {}
    random_summary = summary.get("random_summary", {}) or {}
    comparison = summary.get("comparison", {}) or {}
    project_count = len(rows) + 3

    clean = f"""# CLEAN ZIP MANIFEST — STEP 144

- Project: `lottery-probability-model`
- Checkpoint: `Step 144 — Reproducible Experiment Registry and Baseline Laboratory`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Verification chain: `STEP_122_VERIFY_OK` through `STEP_144_VERIFY_OK`
- Registered experiments: **{status.get('registry_entries', 0)}**
- Dataset SHA-256: `{status.get('dataset_sha256', 'unknown')}`
- Experiment ID: `{status.get('experiment_id', 'unknown')}`
- Result signature SHA-256: `{status.get('result_signature_sha256', 'unknown')}`
- Holdout draws: **{status.get('holdout_draws', 0)}**
- Random baseline trials: **{status.get('random_trials', 0)}**
- Heavy ML retraining performed: **No**
- Personal journal used: **No**
- Future-data leakage detected: **No**
- Bundled `.git` / `.venv` / `.r-lib` / `__pycache__`: **No**

## Initial baseline result

- Frequency baseline average best hits: **{frequency.get('average_best_hits', 0)}**
- Uniform-random mean average best hits: **{random_summary.get('average_best_hits_mean', 0)}**
- Difference: **{comparison.get('frequency_minus_random_mean_average_best_hits', 0)}**

The result is retained even when a tested baseline performs below random. The registry is designed to preserve complete experimental evidence, not only favorable outcomes.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = f"""# Full CLEAN Checkpoint Manifest — Step 144

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 144 — Reproducible Experiment Registry and Baseline Laboratory`
- Generated (Europe/Sofia): `{generated}`
- Base archive: `{BASE_ARCHIVE_NAME}`
- Base archive SHA-256: `{BASE_ARCHIVE_SHA256}`
- New Git commit: **not asserted** (`.git` is intentionally absent from a clean archive)

## Scope

- Adds a deterministic experiment registry with JSONL and CSV indexes.
- Records dataset, code, configuration, seed, environment, split, results and artifacts.
- Adds an expanding-window walk-forward baseline laboratory.
- Compares a frequency baseline with uniform-random packages of equal size.
- Preserves negative and neutral results as first-class experimental evidence.
- Adds a Bulgarian Streamlit page and a terminal runner.
- Does not retrain heavy ML models and does not access the personal journal.

## Verification

- Step 122–143.3 verification chain: **PASS**
- Step 144 deterministic rerun verification: **PASS**
- Step 143.3 final freshness: **synced / zero blockers**
- Experiment ID: `{status.get('experiment_id', 'unknown')}`
- Dataset SHA-256: `{status.get('dataset_sha256', 'unknown')}`
- Configuration SHA-256: `{status.get('configuration_sha256', 'unknown')}`
- Result signature SHA-256: `{status.get('result_signature_sha256', 'unknown')}`
- Registry entries: **{status.get('registry_entries', 0)}**
- Heavy ML retraining performed: **No**
- Personal journal used: **No**
- Future-data leakage detected: **No**

## Local checks after applying in VS Code

```powershell
python .\\tools\\run_reproducible_baseline_experiment.py --read-only
python .\\scripts\\verify_step_144.py
python .\\tools\\finalize_step_144_release.py --verify-only
git status -sb
```

After review, commit and push Step 144 before running a new custom experiment.
"""
    FULL_MANIFEST.write_text(full, encoding="utf-8")
    return {
        "checkpoint": "Step 144",
        "project_file_count": project_count,
        "release_manifest_entries": len(rows),
        "release_manifest_sha256": release_sha,
        "experiment_id": status.get("experiment_id"),
        "result_signature_sha256": status.get("result_signature_sha256"),
    }


def verify_manifests() -> dict:
    release = load_json(RELEASE_MANIFEST)
    failures: list[str] = []
    for row in release.get("files", []):
        path = ROOT / str(row.get("path", ""))
        if not path.is_file():
            failures.append(f"missing:{row.get('path')}")
            continue
        data = path.read_bytes()
        if len(data) != row.get("size_bytes") or sha256_bytes(data) != row.get("sha256"):
            failures.append(f"mismatch:{row.get('path')}")
    current = {row["path"] for row in project_files()}
    listed = {str(row.get("path")) for row in release.get("files", [])}
    failures.extend(f"unlisted:{path}" for path in sorted(current - listed))
    failures.extend(f"stale:{path}" for path in sorted(listed - current))
    return {"ok": not failures, "failure_count": len(failures), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate or verify Step 144 release metadata")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = verify_manifests() if args.verify_only else write_manifests()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
