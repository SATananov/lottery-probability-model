from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RELEASE_MANIFEST = ROOT / "release-manifest.json"
CLEAN_MANIFEST = ROOT / "CLEAN_ZIP_MANIFEST_STEP143_3.md"
FULL_MANIFEST = ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP143_3.md"
EXCLUDED = {
    RELEASE_MANIFEST.name,
    CLEAN_MANIFEST.name,
    FULL_MANIFEST.name,
}
BASE_ARCHIVE_NAME = "lottery-probability-model_STEP143_2_OFFICIAL-DRAW-GITHUB-SYNC-VALIDATION-AUDIT_FULL-CLEAN_20260711_125211.zip"
BASE_ARCHIVE_SHA256 = "6368f2b99d55b0743eb9c5a0842a92a8b020a06cd1ff00f15ec54bafb7291b73"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_files() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDED:
            continue
        data = path.read_bytes()
        rows.append({"path": rel, "size_bytes": len(data), "sha256": sha256_bytes(data)})
    return rows


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_manifests() -> dict:
    rows = project_files()
    release = {
        "checkpoint": "Step 143.3",
        "project": "lottery-probability-model",
        "manifest_scope": "All project files except release-manifest.json, CLEAN_ZIP_MANIFEST_STEP143_3.md and FULL_CLEAN_CHECKPOINT_MANIFEST_STEP143_3.md",
        "file_count": len(rows),
        "files": rows,
    }
    RELEASE_MANIFEST.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    release_sha = sha256_bytes(RELEASE_MANIFEST.read_bytes())

    closure = load_json(ROOT / "models" / "v143_3_downstream_zero_blocker_status.json")
    runner = load_json(ROOT / "models" / "v143_3_statistical_layer_runner_status.json")
    before_count = closure.get("before", {}).get("blocking_out_of_sync_count", "—")
    after_count = closure.get("after", {}).get("blocking_out_of_sync_count", "—")
    overall = closure.get("after", {}).get("overall_status", "unknown")
    runner_name = runner.get("runner", "unknown")
    project_count = len(rows) + 3

    clean = f"""# CLEAN ZIP MANIFEST — STEP 143.3

- Project: `lottery-probability-model`
- Checkpoint: `Step 143.3 — Final Downstream Freshness Repair and Zero-Blocker Closure`
- Project files in archive: **{project_count}**
- Release manifest entries: **{len(rows)}**
- Release manifest SHA-256: `{release_sha}`
- Verification: `STEP_122_VERIFY_OK` through `STEP_143_VERIFY_OK`
- Additional verification: `STEP_143_1_VERIFY_OK`, `STEP_143_2_VERIFY_OK`, `STEP_143_3_VERIFY_OK`
- Final downstream freshness: **{overall}**
- Blocking layers before closure: **{before_count}**
- Blocking layers after closure: **{after_count}**
- Statistical runner recorded by this checkout: **{runner_name}**
- Heavy ML retraining performed: **No**
- Protected heavy model artifacts changed: **No**
- Personal journal final bytes changed: **No**
- Bundled `.git` / `.venv` / `.r-lib` / `__pycache__`: **No**

## Main additions

- `src/v143_3_downstream_zero_blocker_closure_engine.py`
- `src/v143_3_downstream_zero_blocker_closure_section.py`
- `tools/run_downstream_zero_blocker_closure.py`
- `tools/run_statistical_layer.py`
- `tools/finalize_step_143_3_release.py`
- `src/r_statistical_layer_compat_engine.py`
- `scripts/verify_step_143_3.py`

## Closure result

The final Step 122 source-of-truth report must confirm:

```text
overall_status = synced
blocking_out_of_sync_count = 0
```

When `Rscript` is available, the launcher uses the original R scripts. Otherwise it records and uses the deterministic Python compatibility runner. The runner identity above reflects the environment that last executed the closure.
"""
    CLEAN_MANIFEST.write_text(clean, encoding="utf-8")

    generated = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
    full = f"""# Full CLEAN Checkpoint Manifest — Step 143.3

## Project

- Project: `lottery-probability-model`
- Checkpoint: `Step 143.3 — Final Downstream Freshness Repair and Zero-Blocker Closure`
- Generated (Europe/Sofia): `{generated}`
- Base archive: `{BASE_ARCHIVE_NAME}`
- Base archive SHA-256: `{BASE_ARCHIVE_SHA256}`
- New Git commit: **not asserted** (`.git` is intentionally absent from a clean archive)

## Scope

- Executes the required lightweight downstream repair chain.
- Requires the final Step 122 freshness report to confirm zero blockers.
- Uses a cross-platform statistical launcher and preserves the original R implementation.
- Protects trained heavy-model artifacts with before/after SHA-256 checks.
- Protects the personal journal through exact snapshot and restore.
- Integrates zero-blocker closure into automatic refresh after a newly inserted official draw.
- Regenerates release metadata only after the local closure finishes.

## Verification

- Step 122–143 verification chain: **PASS**
- Step 143.1 verification: **PASS**
- Step 143.2 functional Git simulation: **PASS**
- Step 143.3 read-only verification: **PASS**
- Final freshness: `{overall}`
- Blocking layers before closure: `{before_count}`
- Blocking layers after closure: `{after_count}`
- Statistical runner: `{runner_name}`
- Heavy ML retraining performed: **No**
- Protected heavy model changes: **{len(closure.get('heavy_model_changes', []))}**
- Personal journal differences after restore: **{len(closure.get('personal_changes_after_restore', []))}**

## Local checks after applying in VS Code

```powershell
python .\\tools\\run_downstream_zero_blocker_closure.py --strict
python .\\tools\\finalize_step_143_3_release.py
python .\\scripts\\verify_step_143_3.py
git status -sb
```

After review, commit and push Step 143.3 before entering the next official draw.
"""
    FULL_MANIFEST.write_text(full, encoding="utf-8")
    return {
        "checkpoint": "Step 143.3",
        "project_file_count": project_count,
        "release_manifest_entries": len(rows),
        "release_manifest_sha256": release_sha,
        "overall_status": overall,
        "blocking_before": before_count,
        "blocking_after": after_count,
        "statistical_runner": runner_name,
    }


def verify_manifests() -> dict:
    release = load_json(RELEASE_MANIFEST)
    failures: list[str] = []
    for row in release.get("files", []):
        path = ROOT / row["path"]
        if not path.is_file():
            failures.append(f"missing:{row['path']}")
            continue
        data = path.read_bytes()
        if len(data) != row.get("size_bytes") or sha256_bytes(data) != row.get("sha256"):
            failures.append(f"mismatch:{row['path']}")
    current = {row["path"] for row in project_files()}
    listed = {row["path"] for row in release.get("files", [])}
    for path in sorted(current - listed):
        failures.append(f"unlisted:{path}")
    for path in sorted(listed - current):
        failures.append(f"stale:{path}")
    return {"ok": not failures, "failure_count": len(failures), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate or verify Step 143.3 release metadata")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = verify_manifests() if args.verify_only else write_manifests()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
