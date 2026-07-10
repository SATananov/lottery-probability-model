from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.v132_production_incident_evidence_engine import EXPORT_DIR
from src.v134_incident_evidence_registry_engine import REGISTRY_JSONL, load_registry_events

ROOT = Path(__file__).resolve().parents[1]
POLICY_JSON = ROOT / 'models' / 'v135_incident_evidence_retention_policy.json'
STATUS_JSON = ROOT / 'models' / 'v135_incident_evidence_retention_status.json'
SUMMARY_MD = ROOT / 'reports' / 'v135_incident_evidence_retention_summary.md'
AUDIT_JSONL = ROOT / 'reports' / 'v135_incident_evidence_retention_audit.jsonl'
ARCHIVE_DIR = ROOT / 'reports' / 'v135_incident_evidence_archive'

DEFAULT_POLICY: dict[str, Any] = {
    'step': '135',
    'name': 'Incident Evidence Retention, Archive & Safe Cleanup Policy',
    'retention_days_active': 30,
    'archive_cleanup_days': 180,
    'minimum_active_verified_bundles': 10,
    'archive_verified_only': True,
    'protect_invalid_bundles': True,
    'protect_unverified_bundles': True,
    'registry_is_append_only': True,
    'dry_run_default': True,
}

ARCHIVE_CONFIRMATION = 'ARCHIVE VERIFIED EVIDENCE'
CLEANUP_CONFIRMATION = 'DELETE EXPIRED ARCHIVE COPIES'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _parse_utc(value: Any) -> datetime | None:
    text = str(value or '').strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        temp_path = Path(temp_name)
        if temp_path.exists():
            temp_path.unlink()


def load_retention_policy(path: Path = POLICY_JSON) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    if path.exists():
        loaded = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(loaded, dict):
            raise ValueError('Retention policy must be a JSON object.')
        policy.update(loaded)
    for key in ('retention_days_active', 'archive_cleanup_days', 'minimum_active_verified_bundles'):
        policy[key] = max(0, int(policy[key]))
    if policy['archive_cleanup_days'] < policy['retention_days_active']:
        raise ValueError('archive_cleanup_days cannot be lower than retention_days_active.')
    policy['registry_is_append_only'] = True
    policy['dry_run_default'] = True
    return policy


def write_default_policy(path: Path = POLICY_JSON) -> Path:
    if not path.exists():
        _atomic_write_text(path, json.dumps(DEFAULT_POLICY, ensure_ascii=False, indent=2))
    return path


def _bundle_status(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    bundles: dict[str, dict[str, Any]] = {}
    for event in events:
        bundle_id = str(event.get('bundle_id') or '').strip()
        if not bundle_id:
            continue
        row = bundles.setdefault(bundle_id, {
            'bundle_id': bundle_id,
            'created_at_utc': None,
            'latest_event_at_utc': None,
            'latest_verdict': None,
            'archive_sha256': None,
            'source_name': None,
        })
        event_at = event.get('recorded_at_utc')
        if not row['latest_event_at_utc'] or str(event_at or '') >= str(row['latest_event_at_utc'] or ''):
            row['latest_event_at_utc'] = event_at
            if event.get('event_type') in {'VERIFIED', 'INVALID'}:
                row['latest_verdict'] = str(event.get('verdict') or '').lower() or None
        if event.get('event_type') == 'CREATED' and not row['created_at_utc']:
            row['created_at_utc'] = event_at
        row['archive_sha256'] = event.get('archive_sha256') or row['archive_sha256']
        row['source_name'] = event.get('source_name') or row['source_name']
    return bundles


def build_retention_plan(
    *,
    now: datetime | None = None,
    policy: dict[str, Any] | None = None,
    export_dir: Path = EXPORT_DIR,
    archive_dir: Path = ARCHIVE_DIR,
    registry_path: Path = REGISTRY_JSONL,
) -> dict[str, Any]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    active_cutoff = current - timedelta(days=int((policy or load_retention_policy())['retention_days_active']))
    cleanup_cutoff = current - timedelta(days=int((policy or load_retention_policy())['archive_cleanup_days']))
    policy = dict(policy or load_retention_policy())
    events = load_registry_events(registry_path)
    statuses = _bundle_status(events)

    verified_active = []
    for bundle in statuses.values():
        if bundle.get('latest_verdict') == 'verified':
            verified_active.append(bundle)
    verified_active.sort(key=lambda item: str(item.get('created_at_utc') or item.get('latest_event_at_utc') or ''), reverse=True)
    protected_verified_ids = {item['bundle_id'] for item in verified_active[:policy['minimum_active_verified_bundles']]}

    active_rows: list[dict[str, Any]] = []
    archive_candidates: list[dict[str, Any]] = []
    protected_rows: list[dict[str, Any]] = []
    if export_dir.exists():
        for path in sorted(export_dir.glob('*.zip')):
            bundle_id = path.stem
            status = statuses.get(bundle_id, {})
            created = _parse_utc(status.get('created_at_utc')) or datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            verdict = status.get('latest_verdict')
            row = {
                'bundle_id': bundle_id,
                'path': str(path),
                'name': path.name,
                'size_bytes': path.stat().st_size,
                'sha256': _sha256_file(path),
                'created_at_utc': created.isoformat(timespec='seconds'),
                'latest_verdict': verdict or 'unverified',
                'reason': '',
            }
            if verdict == 'invalid' and policy['protect_invalid_bundles']:
                row['reason'] = 'INVALID evidence is protected for investigation.'
                protected_rows.append(row)
            elif verdict != 'verified' and policy['protect_unverified_bundles']:
                row['reason'] = 'Unverified evidence is protected until integrity verification.'
                protected_rows.append(row)
            elif bundle_id in protected_verified_ids:
                row['reason'] = 'Protected by minimum_active_verified_bundles.'
                protected_rows.append(row)
            elif created >= active_cutoff:
                row['reason'] = 'Inside active retention window.'
                active_rows.append(row)
            elif verdict == 'verified':
                row['reason'] = 'Verified and older than active retention window.'
                archive_candidates.append(row)
            else:
                row['reason'] = 'Fail-closed: not eligible for archive.'
                protected_rows.append(row)

    cleanup_candidates: list[dict[str, Any]] = []
    archive_rows: list[dict[str, Any]] = []
    if archive_dir.exists():
        for path in sorted(archive_dir.glob('*.zip')):
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            row = {
                'name': path.name,
                'path': str(path),
                'size_bytes': path.stat().st_size,
                'sha256': _sha256_file(path),
                'modified_at_utc': modified.isoformat(timespec='seconds'),
            }
            if modified < cleanup_cutoff:
                cleanup_candidates.append(row)
            else:
                archive_rows.append(row)

    return {
        'step': '135',
        'name': DEFAULT_POLICY['name'],
        'generated_at_utc': current.isoformat(timespec='seconds'),
        'dry_run': True,
        'production_state_changed': False,
        'registry_modified': False,
        'policy': policy,
        'counts': {
            'active': len(active_rows),
            'protected': len(protected_rows),
            'archive_candidates': len(archive_candidates),
            'archived_retained': len(archive_rows),
            'cleanup_candidates': len(cleanup_candidates),
        },
        'active': active_rows,
        'protected': protected_rows,
        'archive_candidates': archive_candidates,
        'archived_retained': archive_rows,
        'cleanup_candidates': cleanup_candidates,
    }


def _append_audit(event: dict[str, Any], path: Path = AUDIT_JSONL) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8', newline='') as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def apply_archive_plan(
    plan: dict[str, Any], *, confirmation: str, archive_dir: Path = ARCHIVE_DIR, audit_path: Path = AUDIT_JSONL,
) -> dict[str, Any]:
    if confirmation != ARCHIVE_CONFIRMATION:
        raise PermissionError('Exact archive confirmation phrase is required.')
    archive_dir.mkdir(parents=True, exist_ok=True)
    moved: list[dict[str, Any]] = []
    for item in plan.get('archive_candidates', []):
        source = Path(item['path'])
        if not source.is_file() or _sha256_file(source) != item['sha256']:
            raise RuntimeError(f'Archive candidate changed after preview: {source.name}')
        target = archive_dir / source.name
        if target.exists():
            if _sha256_file(target) != item['sha256']:
                raise RuntimeError(f'Archive collision with different content: {target.name}')
            source.unlink()
        else:
            shutil.move(str(source), str(target))
        moved.append({'bundle_id': item['bundle_id'], 'name': target.name, 'sha256': item['sha256']})
    event = {
        'step': '135', 'event_type': 'ARCHIVE_APPLIED', 'recorded_at_utc': utc_now(),
        'item_count': len(moved), 'items': moved, 'registry_modified': False,
        'production_state_changed': False,
    }
    _append_audit(event, audit_path)
    return event


def apply_cleanup_plan(
    plan: dict[str, Any], *, confirmation: str, audit_path: Path = AUDIT_JSONL,
) -> dict[str, Any]:
    if confirmation != CLEANUP_CONFIRMATION:
        raise PermissionError('Exact cleanup confirmation phrase is required.')
    deleted: list[dict[str, Any]] = []
    for item in plan.get('cleanup_candidates', []):
        path = Path(item['path'])
        if not path.is_file() or _sha256_file(path) != item['sha256']:
            raise RuntimeError(f'Cleanup candidate changed after preview: {path.name}')
        path.unlink()
        deleted.append({'name': item['name'], 'sha256': item['sha256']})
    event = {
        'step': '135', 'event_type': 'CLEANUP_APPLIED', 'recorded_at_utc': utc_now(),
        'item_count': len(deleted), 'items': deleted, 'registry_modified': False,
        'production_state_changed': False,
    }
    _append_audit(event, audit_path)
    return event


def write_retention_status(plan: dict[str, Any]) -> None:
    summary = (
        '# Step 135 — Incident Evidence Retention, Archive & Safe Cleanup Policy\n\n'
        f"- Generated UTC: **{plan['generated_at_utc']}**\n"
        f"- Active: **{plan['counts']['active']}**\n"
        f"- Protected: **{plan['counts']['protected']}**\n"
        f"- Archive candidates: **{plan['counts']['archive_candidates']}**\n"
        f"- Cleanup candidates: **{plan['counts']['cleanup_candidates']}**\n\n"
        'Preview is read-only. Registry history remains append-only and is never removed by this policy.\n'
    )
    payload = dict(plan)
    payload['summary_md'] = summary
    _atomic_write_text(STATUS_JSON, json.dumps(payload, ensure_ascii=False, indent=2))
    _atomic_write_text(SUMMARY_MD, summary)
