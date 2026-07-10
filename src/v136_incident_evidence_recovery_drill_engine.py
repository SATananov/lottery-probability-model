from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v133_incident_evidence_integrity_engine import inspect_incident_evidence_zip
from src.v134_incident_evidence_registry_engine import REGISTRY_JSONL, load_registry_events
from src.v135_incident_evidence_retention_engine import ARCHIVE_DIR

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v136_incident_evidence_recovery_drill_status.json'
SUMMARY_MD = ROOT / 'reports' / 'v136_incident_evidence_recovery_drill_summary.md'
AUDIT_JSONL = ROOT / 'reports' / 'v136_incident_evidence_recovery_drill_audit.jsonl'
STAGING_ROOT = ROOT / 'reports' / 'v136_recovery_drill_staging'
DRILL_CONFIRMATION = 'RUN ISOLATED RECOVERY DRILL'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _latest_registry_record(bundle_id: str, registry_path: Path = REGISTRY_JSONL) -> dict[str, Any] | None:
    matches = [e for e in load_registry_events(registry_path) if str(e.get('bundle_id') or '') == bundle_id]
    return matches[-1] if matches else None


def build_recovery_drill_plan(*, archive_dir: Path = ARCHIVE_DIR, registry_path: Path = REGISTRY_JSONL) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if archive_dir.exists():
        for path in sorted(archive_dir.glob('*.zip')):
            bundle_id = path.stem
            registry = _latest_registry_record(bundle_id, registry_path)
            actual_sha = _sha256_file(path)
            expected_sha = (registry or {}).get('archive_sha256')
            eligible = bool(registry and str(registry.get('verdict') or '').lower() == 'verified' and expected_sha == actual_sha)
            reason = 'Eligible: archived, registry-verified and SHA-256 matches.' if eligible else 'Protected: missing VERIFIED registry record or SHA-256 mismatch.'
            rows.append({
                'bundle_id': bundle_id,
                'path': str(path),
                'name': path.name,
                'size_bytes': path.stat().st_size,
                'actual_sha256': actual_sha,
                'expected_sha256': expected_sha,
                'latest_verdict': (registry or {}).get('verdict') or 'unknown',
                'eligible': eligible,
                'reason': reason,
            })
    return {
        'step': '136',
        'name': 'Incident Evidence Recovery Drill & Restore Validation',
        'generated_at_utc': utc_now(),
        'read_only_preview': True,
        'production_state_changed': False,
        'registry_modified': False,
        'archive_modified': False,
        'candidate_count': len(rows),
        'eligible_count': sum(1 for row in rows if row['eligible']),
        'candidates': rows,
    }


def run_recovery_drill(
    archive_path: Path,
    *,
    confirmation: str,
    registry_path: Path = REGISTRY_JSONL,
    staging_root: Path = STAGING_ROOT,
    retain_staging_copy: bool = False,
    audit_path: Path = AUDIT_JSONL,
) -> dict[str, Any]:
    if confirmation != DRILL_CONFIRMATION:
        raise PermissionError('Exact recovery drill confirmation phrase is required.')
    archive_path = archive_path.resolve()
    if not archive_path.is_file() or archive_path.suffix.lower() != '.zip':
        raise FileNotFoundError('Recovery drill source ZIP does not exist.')

    bundle_id = archive_path.stem
    registry = _latest_registry_record(bundle_id, registry_path)
    source_sha = _sha256_file(archive_path)
    expected_sha = (registry or {}).get('archive_sha256')
    if not registry or str(registry.get('verdict') or '').lower() != 'verified':
        raise RuntimeError('Fail-closed: bundle has no latest VERIFIED registry record.')
    if source_sha != expected_sha:
        raise RuntimeError('Fail-closed: archived ZIP SHA-256 does not match registry.')

    staging_root.mkdir(parents=True, exist_ok=True)
    drill_id = f"DRILL-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{bundle_id}"
    work_dir = Path(tempfile.mkdtemp(prefix=f'{drill_id}-', dir=staging_root))
    staged_zip = work_dir / archive_path.name
    try:
        shutil.copy2(archive_path, staged_zip)
        staged_sha = _sha256_file(staged_zip)
        if staged_sha != source_sha:
            raise RuntimeError('Staging copy SHA-256 mismatch.')
        inspection = inspect_incident_evidence_zip(staged_zip.read_bytes(), source_name=staged_zip.name, write_outputs=False)
        restored_identity_ok = inspection.get('bundle_id') == bundle_id
        passed = inspection.get('verdict') == 'verified' and restored_identity_ok
        result = {
            'step': '136',
            'drill_id': drill_id,
            'completed_at_utc': utc_now(),
            'bundle_id': bundle_id,
            'source_path': str(archive_path),
            'source_sha256': source_sha,
            'staged_sha256': staged_sha,
            'registry_sha256': expected_sha,
            'integrity_verdict': inspection.get('verdict'),
            'restored_identity_ok': restored_identity_ok,
            'drill_verdict': 'passed' if passed else 'failed',
            'failed_check_count': inspection.get('failed_check_count'),
            'staging_retained': bool(retain_staging_copy),
            'staging_path': str(work_dir) if retain_staging_copy else None,
            'production_state_changed': False,
            'registry_modified': False,
            'archive_modified': False,
            'automatic_production_restore_performed': False,
        }
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_path.open('a', encoding='utf-8', newline='') as handle:
            handle.write(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
            handle.flush(); os.fsync(handle.fileno())
        if archive_path.exists() and _sha256_file(archive_path) != source_sha:
            raise RuntimeError('Source archive changed during drill.')
        return result
    finally:
        if not retain_staging_copy:
            shutil.rmtree(work_dir, ignore_errors=True)


def write_recovery_drill_status(result: dict[str, Any]) -> None:
    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    SUMMARY_MD.write_text(
        '# Step 136 — Incident Evidence Recovery Drill & Restore Validation\n\n'
        f"- Drill verdict: **{str(result.get('drill_verdict')).upper()}**\n"
        f"- Bundle ID: **{result.get('bundle_id')}**\n"
        f"- Integrity verdict: **{result.get('integrity_verdict')}**\n"
        f"- Production state changed: **{result.get('production_state_changed')}**\n"
        f"- Automatic production restore: **{result.get('automatic_production_restore_performed')}**\n",
        encoding='utf-8',
    )
