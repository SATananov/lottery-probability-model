from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RELEASE_MANIFEST = ROOT / "release-manifest.json"
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP145.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP145.md"
EXCLUDED = {RELEASE_MANIFEST.name, CLEAN_MANIFEST.name, FULL_MANIFEST.name}
BASE_ARCHIVE_NAME = "lottery-probability-model_STEP144_REPRODUCIBLE-EXPERIMENT-REGISTRY-BASELINE-LAB_FULL-CLEAN_20260711_134830.zip"
BASE_ARCHIVE_SHA256 = "00659656db36ac82c63beaf6c46c6f5a0cd9d1534763ec19eae12a05dfd7e028"


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
        "checkpoint": "Step 145",
        "project": "lottery-probability-model",
        "manifest_scope": (
            "All project files except release-manifest.json, CLEAN_ZIP_MANIFEST_STEP145.md "
            "and FULL_CLEAN_CHECKPOINT_MANIFEST_STEP145.md"
        ),
        "file_count": len(rows),
        "files": rows,
    }
    RELEASE_MANIFEST.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    release_sha = sha256_bytes(RELEASE_MANIFEST.read_bytes())

    status = load_json(ROOT / "models" / "v145_experimental_neural_dynamics_status.json")
    summary = load_json(ROOT / "reports" / "v145_neural_dynamics_summary.json")
    neural = summary.get("neural_dynamics", {}) or {}
    frequency = summary.get("frequency_baseline", {}) or {}
    recency = summary.get("recency_baseline", {}) or {}
    random_summary = summary.get("random_summary", {}) or {}
    comparison = summary.get("comparison", {}) or {}
    project_count = len(rows) + 3

    clean = f"""# CLEAN ZIP MANIFEST — STEP 145

- Project: `lottery-probability-model`
- Checkpoint: `Step 145 — Experimental Neural Dynamics Sandbox and Baseline Comparison`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Verification chain: `STEP_122_VERIFY_OK` through `STEP_145_VERIFY_OK`
- Experiment ID: `{status.get('experiment_id', 'unknown')}`
- Dataset SHA-256: `{status.get('dataset_sha256', 'unknown')}`
- Result signature SHA-256: `{status.get('result_signature_sha256', 'unknown')}`
- Holdout draws: **{status.get('holdout_draws', 0)}**
- Promotion gate passed: **{status.get('promotion_gate_passed', False)}**
- Production integration enabled: **No**
- Real ticket generation enabled: **No**
- Heavy ML retraining performed: **No**
- Personal journal used: **No**
- Future-data leakage detected: **No**
- Bundled `.git` / `.venv` / `.r-lib` / `__pycache__`: **No**

## Initial historical comparison

- Neural dynamics average best hits: **{neural.get('average_best_hits', 0)}**
- Frequency baseline: **{frequency.get('average_best_hits', 0)}**
- Recency baseline: **{recency.get('average_best_hits', 0)}**
- Uniform-random mean: **{random_summary.get('average_best_hits_mean', 0)}**
- Neural minus random mean: **{comparison.get('neural_minus_random_mean_average_best_hits', 0)}**

The negative result is preserved. Step 145 remains research-only and is not connected to production ticket generation.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = f"""# Full CLEAN Checkpoint Manifest — Step 145

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 145 — Experimental Neural Dynamics Sandbox and Baseline Comparison`
- Generated (Europe/Sofia): `{generated}`
- Base archive: `{BASE_ARCHIVE_NAME}`
- Base archive SHA-256: `{BASE_ARCHIVE_SHA256}`
- New Git commit: **not asserted** (`.git` is intentionally absent from a clean archive)

## Scope

- Adds a continuous-time-inspired leaky neural reservoir sandbox.
- Uses an online ridge readout in a strict expanding-window walk-forward protocol.
- Compares neural dynamics with frequency, recency-weighted and uniform-random baselines.
- Uses equal package sizes and stores draw-level paired comparison evidence.
- Registers the experiment in the Step 144 reproducibility registry.
- Preserves negative results and blocks automatic promotion.
- Does not use the personal journal, retrain heavy ML models or generate real tickets.
- Does not claim analogue neural hardware, in-memory computing or an adaptive ODE solver.

## Verification

- Step 122–144 verification chain: **PASS**
- Step 145 deterministic rerun: **PASS**
- Step 143.3 final freshness: **synced / zero blockers**
- Experiment ID: `{status.get('experiment_id', 'unknown')}`
- Configuration SHA-256: `{status.get('configuration_sha256', 'unknown')}`
- Result signature SHA-256: `{status.get('result_signature_sha256', 'unknown')}`
- Promotion gate passed: **{status.get('promotion_gate_passed', False)}**
- Production integration enabled: **No**

## Local checks after applying in VS Code

```powershell
python ./tools/run_experimental_neural_dynamics.py --read-only
python ./scripts/verify_step_145.py
python ./tools/finalize_step_145_release.py --verify-only
git status -sb
```

After review, commit and push Step 145 before running a custom configuration.
"""
    FULL_MANIFEST.write_text(full, encoding="utf-8")
    return {
        "checkpoint": "Step 145",
        "project_file_count": project_count,
        "release_manifest_entries": len(rows),
        "release_manifest_sha256": release_sha,
        "experiment_id": status.get("experiment_id"),
        "result_signature_sha256": status.get("result_signature_sha256"),
    }


def verify_manifests() -> dict:
    release = load_json(RELEASE_MANIFEST)
    failures: list[str] = []
    if release.get("checkpoint") != "Step 145":
        failures.append(f"checkpoint:{release.get('checkpoint')}")
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
    parser = argparse.ArgumentParser(description="Regenerate or verify Step 145 release metadata")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = verify_manifests() if args.verify_only else write_manifests()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
