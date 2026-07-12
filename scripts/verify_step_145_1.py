from __future__ import annotations

import json
import py_compile
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v122_unified_official_draw_freshness_engine import (
    REPORT_CSV as V122_CSV,
    REPORT_JSON as V122_REPORT,
    STATUS_JSON as V122_STATUS,
    SUMMARY_MD as V122_SUMMARY,
    build_freshness_report,
)
from src.v123_bst_official_draw_detection_engine import (
    REPORT_JSON as V123_REPORT,
    STATUS_JSON as V123_STATUS,
    SUMMARY_MD as V123_SUMMARY,
    write_detection_outputs,
)
from src.v126_startup_automation_engine import (
    AUDIT_JSONL as V126_AUDIT,
    REPORT_JSON as V126_REPORT,
    STATUS_JSON as V126_STATUS,
    SUMMARY_MD as V126_SUMMARY,
    _write_outputs as write_v126_outputs,
    load_status,
)
from src.v145_1_release_artifact_integrity import (
    ARCHIVE_ROOT_NAME,
    POLICY_VERSION,
    build_clean_zip,
    collect_release_rows,
    forbidden_release_reason,
    validate_release_manifest,
)
from src.v145_1_runtime_artifact_integrity import RUNTIME_ROOT, load_json

REQUIRED = [
    ROOT / "src" / "v145_1_release_artifact_integrity.py",
    ROOT / "src" / "v145_1_runtime_artifact_integrity.py",
    ROOT / "tools" / "finalize_step_145_1_release.py",
    ROOT / "scripts" / "verify_step_145_1.py",
    ROOT / "models" / "v145_1_release_artifact_integrity_policy.json",
    ROOT / "reports" / "STEP_145_1_CLEAN_RELEASE_METADATA_RUNTIME_ARTIFACT_INTEGRITY_REPAIR.md",
    ROOT / "release-manifest.json",
]
CANONICAL_RUNTIME_ARTIFACTS = [
    V122_STATUS, V122_REPORT, V122_CSV, V122_SUMMARY,
    V123_STATUS, V123_REPORT, V123_SUMMARY,
    V126_STATUS, V126_REPORT, V126_SUMMARY, V126_AUDIT,
]


def file_hash(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(paths: list[Path]) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): file_hash(path) for path in paths if path.is_file()}


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"Missing: {path.relative_to(ROOT)}")
    for path in [item for item in REQUIRED if item.suffix == ".py"] + [
        ROOT / "src/v122_unified_official_draw_freshness_engine.py",
        ROOT / "src/v123_bst_official_draw_detection_engine.py",
        ROOT / "src/v126_startup_automation_engine.py",
        ROOT / "tools/finalize_step_143_3_release.py",
        ROOT / "tools/finalize_step_144_release.py",
        ROOT / "tools/finalize_step_145_release.py",
    ]:
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    release = load_json(ROOT / "release-manifest.json")
    validation = validate_release_manifest(release, root=ROOT)
    if release.get("checkpoint") not in {"Step 145.1", "Step 146", "Step 147", "Step 148", "Step 149", "Step 150", "Step 150.1", "Step 150.2"}:
        failures.append(f"Unexpected release checkpoint: {release.get('checkpoint')}")
    failures.extend(validation.get("failures", []))
    if release.get("release_policy_version") != POLICY_VERSION:
        failures.append("Release policy version mismatch")

    rows = collect_release_rows(root=ROOT)
    forbidden_rows = [row["path"] for row in rows if forbidden_release_reason(row["path"]) is not None]
    if forbidden_rows:
        failures.append("Forbidden rows collected: " + ", ".join(forbidden_rows[:20]))
    listed = {str(row.get("path")) for row in release.get("files", [])}
    for forbidden_prefix in (".git/", ".venv/", "venv/", ".r-lib/", "reports/runtime/"):
        if any(path == forbidden_prefix.rstrip("/") or path.startswith(forbidden_prefix) for path in listed):
            failures.append(f"Manifest contains forbidden prefix: {forbidden_prefix}")

    for finalizer in (
        ROOT / "tools/finalize_step_143_3_release.py",
        ROOT / "tools/finalize_step_144_release.py",
        ROOT / "tools/finalize_step_145_release.py",
    ):
        text = finalizer.read_text(encoding="utf-8")
        if "collect_release_rows" not in text or "validate_release_manifest" not in text:
            failures.append(f"Legacy finalizer does not use shared policy: {finalizer.name}")

    before = snapshot(CANONICAL_RUNTIME_ARTIFACTS)
    audit_size_before = V126_AUDIT.stat().st_size if V126_AUDIT.exists() else 0

    build_freshness_report(write_outputs=True)

    detection = load_json(V123_STATUS)
    if detection:
        detection = deepcopy(detection)
        detection["checked_at_utc"] = "2099-01-01T00:00:00+00:00"
        detection["source_diagnostics"] = {"html_sha256": "volatile", "html_bytes": 1}
        write_detection_outputs(detection)
    else:
        failures.append("Step 123 canonical status is missing")

    startup = load_json(V126_STATUS)
    if startup:
        startup = deepcopy(startup)
        startup["started_at_utc"] = "2099-01-01T00:00:00+00:00"
        startup["checked_at_utc"] = "2099-01-01T00:00:01+00:00"
        startup["finished_at_utc"] = "2099-01-01T00:00:02+00:00"
        startup["trigger"] = "manual_check"
        if isinstance(startup.get("detection"), dict):
            startup["detection"]["checked_at_utc"] = "2099-01-01T00:00:01+00:00"
            startup["detection"]["source_diagnostics"] = {"html_sha256": "volatile"}
        write_v126_outputs(startup)
    else:
        failures.append("Step 126 canonical status is missing")

    after = snapshot(CANONICAL_RUNTIME_ARTIFACTS)
    if before != after:
        changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        failures.append("Volatile runtime checks changed tracked snapshots: " + ", ".join(changed))
    audit_size_after = V126_AUDIT.stat().st_size if V126_AUDIT.exists() else 0
    if audit_size_before != audit_size_after:
        failures.append("Step 126 canonical audit appended a duplicate runtime event")
    if not RUNTIME_ROOT.is_dir():
        failures.append("Ignored runtime artifact directory was not created")
    runtime_status = load_status()
    if not runtime_status:
        failures.append("Step 126 does not load current ignored runtime state")

    checkpoint_metadata = {
        "Step 145.1": (ROOT / "CLEAN_ZIP_MANIFEST_STEP145_1.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP145_1.md"),
        "Step 146": (ROOT / "CLEAN_ZIP_MANIFEST_STEP146.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP146.md"),
        "Step 147": (ROOT / "CLEAN_ZIP_MANIFEST_STEP147.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP147.md"),
        "Step 148": (ROOT / "CLEAN_ZIP_MANIFEST_STEP148.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP148.md"),
        "Step 149": (ROOT / "CLEAN_ZIP_MANIFEST_STEP149.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP149.md"),
        "Step 150": (ROOT / "CLEAN_ZIP_MANIFEST_STEP150.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150.md"),
        "Step 150.1": (ROOT / "CLEAN_ZIP_MANIFEST_STEP150_1.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_1.md"),
        "Step 150.2": (ROOT / "CLEAN_ZIP_MANIFEST_STEP150_2.md", ROOT / "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP150_2.md"),
    }
    metadata_pair = checkpoint_metadata.get(
        str(release.get("checkpoint")),
        checkpoint_metadata["Step 145.1"],
    )
    if not all(path.is_file() for path in metadata_pair):
        failures.append("Current clean checkpoint metadata files are missing")

    with tempfile.TemporaryDirectory(prefix="step145_1_verify_") as tmp:
        archive_path = Path(tmp) / "step145_1_clean.zip"
        result = build_clean_zip(
            archive_path,
            root=ROOT,
            metadata_files=(
                ROOT / "release-manifest.json",
                metadata_pair[0],
                metadata_pair[1],
            ),
        )
        if result.get("forbidden_entries"):
            failures.append("Clean ZIP builder returned forbidden entries")
        with zipfile.ZipFile(archive_path, "r") as archive:
            if archive.testzip() is not None:
                failures.append("Clean ZIP CRC validation failed")
            for name in archive.namelist():
                parts = Path(name).parts
                if not parts or parts[0] != ARCHIVE_ROOT_NAME:
                    failures.append(f"ZIP entry outside project root: {name}")
                    break
                rel = Path(*parts[1:]).as_posix()
                reason = forbidden_release_reason(rel) if rel else None
                if reason not in {None, "release_metadata_managed_separately"}:
                    failures.append(f"Forbidden ZIP entry: {name} ({reason})")
                    break

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if "reports/runtime/v145_1_artifact_integrity/" not in gitignore:
        failures.append("Step 145.1 runtime path is not ignored by Git")
    for local_path in ("data/user_journal.db", "data/user_journal_exports/"):
        if local_path not in gitignore:
            failures.append(f"Local personal journal path is not ignored: {local_path}")

    if failures:
        for failure in failures:
            print("STEP_145_1_VERIFY_FAIL", failure)
        return 1
    print("STEP_145_1_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
