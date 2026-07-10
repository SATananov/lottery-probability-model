from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_JSONL = ROOT / 'reports' / 'v134_incident_evidence_registry.jsonl'
STATUS_JSON = ROOT / 'models' / 'v134_incident_evidence_registry_status.json'
SUMMARY_MD = ROOT / 'reports' / 'v134_incident_evidence_registry_summary.md'

ALLOWED_EVENT_TYPES = {'CREATED', 'VERIFIED', 'INVALID'}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def _event_id(payload: dict[str, Any]) -> str:
    basis = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return f"EVT-{_sha256(basis)[:20].upper()}"


def _normalize_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = str(payload.get('event_type') or '').upper()
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f'Unsupported registry event type: {event_type}')
    base = {
        'step': '134',
        'event_type': event_type,
        'recorded_at_utc': str(payload.get('recorded_at_utc') or utc_now()),
        'bundle_id': payload.get('bundle_id'),
        'archive_sha256': payload.get('archive_sha256'),
        'archive_size_bytes': int(payload.get('archive_size_bytes') or 0),
        'source_name': Path(str(payload.get('source_name') or 'unknown.zip')).name,
        'verdict': payload.get('verdict'),
        'failure_stage': payload.get('failure_stage'),
        'health': payload.get('health'),
        'failed_check_count': int(payload.get('failed_check_count') or 0),
        'reason': str(payload.get('reason') or ''),
        'read_only': True,
        'production_state_changed': False,
    }
    base['event_id'] = _event_id(base)
    return base


def load_registry_events(path: Path = REGISTRY_JSONL) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Invalid registry JSONL at line {line_number}: {exc}') from exc
        if not isinstance(item, dict):
            raise ValueError(f'Invalid registry entry at line {line_number}.')
        events.append(item)
    return events


def _build_status(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(events)
    bundles: dict[str, dict[str, Any]] = {}
    for event in rows:
        bundle_id = str(event.get('bundle_id') or 'UNKNOWN')
        current = bundles.setdefault(bundle_id, {
            'bundle_id': bundle_id,
            'created_at_utc': None,
            'last_checked_at_utc': None,
            'archive_sha256': event.get('archive_sha256'),
            'latest_verdict': None,
            'verification_count': 0,
            'invalid_count': 0,
            'failure_stage': event.get('failure_stage'),
            'health': event.get('health'),
        })
        current['archive_sha256'] = event.get('archive_sha256') or current['archive_sha256']
        current['failure_stage'] = event.get('failure_stage') or current['failure_stage']
        current['health'] = event.get('health') or current['health']
        if event.get('event_type') == 'CREATED':
            current['created_at_utc'] = current['created_at_utc'] or event.get('recorded_at_utc')
        elif event.get('event_type') in {'VERIFIED', 'INVALID'}:
            current['last_checked_at_utc'] = event.get('recorded_at_utc')
            current['latest_verdict'] = str(event.get('verdict') or '').lower() or None
            current['verification_count'] += 1
            if event.get('event_type') == 'INVALID':
                current['invalid_count'] += 1
    bundle_rows = sorted(bundles.values(), key=lambda item: (item.get('created_at_utc') or '', item['bundle_id']), reverse=True)
    return {
        'step': '134',
        'name': 'Incident Evidence Registry & Verification History',
        'updated_at_utc': utc_now(),
        'read_only_registry_view': True,
        'production_state_changed': False,
        'event_count': len(rows),
        'bundle_count': len(bundle_rows),
        'created_count': sum(1 for item in rows if item.get('event_type') == 'CREATED'),
        'verified_count': sum(1 for item in rows if item.get('event_type') == 'VERIFIED'),
        'invalid_count': sum(1 for item in rows if item.get('event_type') == 'INVALID'),
        'bundles': bundle_rows,
    }


def _summary(status: dict[str, Any]) -> str:
    return (
        '# Step 134 — Incident Evidence Registry & Verification History\n\n'
        f"- Updated UTC: **{status['updated_at_utc']}**\n"
        f"- Registered bundles: **{status['bundle_count']}**\n"
        f"- Registry events: **{status['event_count']}**\n"
        f"- Created events: **{status['created_count']}**\n"
        f"- Verified events: **{status['verified_count']}**\n"
        f"- Invalid events: **{status['invalid_count']}**\n\n"
        'The registry stores metadata and cryptographic fingerprints only. It does not store archive contents or secrets.\n'
    )


def rebuild_registry_status(*, write_outputs: bool = True, path: Path = REGISTRY_JSONL) -> dict[str, Any]:
    status = _build_status(load_registry_events(path))
    status['summary_md'] = _summary(status)
    if write_outputs and path == REGISTRY_JSONL:
        _atomic_write_text(STATUS_JSON, json.dumps(status, ensure_ascii=False, indent=2))
        _atomic_write_text(SUMMARY_MD, status['summary_md'])
    return status


def append_registry_event(payload: dict[str, Any], *, path: Path = REGISTRY_JSONL) -> dict[str, Any]:
    event = _normalize_event(payload)
    events = load_registry_events(path)
    if not any(item.get('event_id') == event['event_id'] for item in events):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8', newline='') as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
    if path == REGISTRY_JSONL:
        rebuild_registry_status(write_outputs=True, path=path)
    return event


def register_bundle_created(evidence: dict[str, Any], archive_bytes: bytes, *, source_name: str | None = None, path: Path = REGISTRY_JSONL) -> dict[str, Any]:
    snapshot = evidence.get('operations_snapshot', {})
    bst = snapshot.get('bst', {})
    return append_registry_event({
        'event_type': 'CREATED',
        'bundle_id': evidence.get('bundle_id'),
        'archive_sha256': _sha256(archive_bytes),
        'archive_size_bytes': len(archive_bytes),
        'source_name': source_name or f"{evidence.get('bundle_id') or 'INC-UNKNOWN'}.zip",
        'verdict': 'created',
        'failure_stage': bst.get('failure_stage'),
        'health': snapshot.get('health'),
        'reason': 'Incident evidence bundle created read-only.',
    }, path=path)


def register_verification_result(result: dict[str, Any], *, path: Path = REGISTRY_JSONL) -> dict[str, Any]:
    verdict = str(result.get('verdict') or 'invalid').lower()
    failed = [item for item in result.get('checks', []) if not item.get('passed')]
    reason = '; '.join(f"{item.get('code')}: {item.get('message')}" for item in failed[:5])
    if not reason:
        reason = 'All integrity and chain-of-custody checks passed.'
    return append_registry_event({
        'event_type': 'VERIFIED' if verdict == 'verified' else 'INVALID',
        'bundle_id': result.get('bundle_id'),
        'archive_sha256': result.get('archive_sha256'),
        'archive_size_bytes': result.get('archive_size_bytes'),
        'source_name': result.get('source_name'),
        'verdict': verdict,
        'failed_check_count': result.get('failed_check_count'),
        'reason': reason,
    }, path=path)


def registry_events_csv(events: Iterable[dict[str, Any]]) -> bytes:
    rows = list(events)
    fields = [
        'event_id', 'recorded_at_utc', 'event_type', 'bundle_id', 'archive_sha256',
        'archive_size_bytes', 'source_name', 'verdict', 'failure_stage', 'health',
        'failed_check_count', 'reason',
    ]
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode('utf-8-sig')
