from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v134_incident_evidence_registry_engine import REGISTRY_JSONL, load_registry_events
from src.v136_incident_evidence_recovery_drill_engine import AUDIT_JSONL as DRILL_AUDIT_JSONL

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v137_recovery_drill_reconciliation_status.json'
SUMMARY_MD = ROOT / 'reports' / 'v137_recovery_drill_reconciliation_summary.md'
EXCEPTION_AUDIT_JSONL = ROOT / 'reports' / 'v137_recovery_drill_exception_closure_audit.jsonl'
CLOSE_CONFIRMATION = 'CLOSE RECOVERY DRILL EXCEPTION'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as handle:
            handle.write(text)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        temp_path = Path(temp_name)
        if temp_path.exists():
            temp_path.unlink()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Invalid JSONL at {path.name}:{line_number}: {exc}') from exc
        if not isinstance(item, dict):
            raise ValueError(f'Invalid JSONL object at {path.name}:{line_number}.')
        rows.append(item)
    return rows


def _latest_registry_by_bundle(registry_path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in load_registry_events(registry_path):
        bundle_id = str(event.get('bundle_id') or '').strip()
        if bundle_id:
            latest[bundle_id] = event
    return latest


def _closed_exception_ids(path: Path) -> set[str]:
    return {
        str(row.get('exception_id') or '')
        for row in _load_jsonl(path)
        if row.get('event_type') == 'EXCEPTION_CLOSED'
    }


def _exception_id(drill: dict[str, Any], codes: list[str]) -> str:
    payload = '|'.join([
        str(drill.get('drill_id') or ''),
        str(drill.get('bundle_id') or ''),
        ','.join(sorted(codes)),
    ])
    return 'EXC-' + hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16].upper()


def build_reconciliation_status(
    *,
    drill_audit_path: Path = DRILL_AUDIT_JSONL,
    registry_path: Path = REGISTRY_JSONL,
    closure_audit_path: Path = EXCEPTION_AUDIT_JSONL,
) -> dict[str, Any]:
    drills = _load_jsonl(drill_audit_path)
    registry = _latest_registry_by_bundle(registry_path)
    closed_ids = _closed_exception_ids(closure_audit_path)
    rows: list[dict[str, Any]] = []
    for drill in drills:
        bundle_id = str(drill.get('bundle_id') or '')
        reg = registry.get(bundle_id)
        codes: list[str] = []
        if reg is None:
            codes.append('REGISTRY_RECORD_MISSING')
        else:
            if str(reg.get('verdict') or '').lower() != 'verified':
                codes.append('LATEST_REGISTRY_NOT_VERIFIED')
            if str(reg.get('archive_sha256') or '') != str(drill.get('source_sha256') or ''):
                codes.append('REGISTRY_SHA_MISMATCH')
        if str(drill.get('source_sha256') or '') != str(drill.get('staged_sha256') or ''):
            codes.append('STAGING_SHA_MISMATCH')
        if str(drill.get('drill_verdict') or '').lower() != 'passed':
            codes.append('DRILL_NOT_PASSED')
        if str(drill.get('integrity_verdict') or '').lower() != 'verified':
            codes.append('INTEGRITY_NOT_VERIFIED')
        if drill.get('automatic_production_restore_performed') is not False:
            codes.append('AUTOMATIC_RESTORE_FLAG_UNSAFE')
        if drill.get('production_state_changed') is not False:
            codes.append('PRODUCTION_STATE_CHANGED')
        exception_id = _exception_id(drill, codes) if codes else None
        closed = bool(exception_id and exception_id in closed_ids)
        rows.append({
            'drill_id': drill.get('drill_id'),
            'bundle_id': bundle_id,
            'completed_at_utc': drill.get('completed_at_utc'),
            'drill_verdict': drill.get('drill_verdict'),
            'integrity_verdict': drill.get('integrity_verdict'),
            'registry_verdict': (reg or {}).get('verdict') or 'missing',
            'source_sha256': drill.get('source_sha256'),
            'registry_sha256': (reg or {}).get('archive_sha256'),
            'exception_id': exception_id,
            'exception_codes': codes,
            'exception_closed': closed,
            'reconciliation_status': 'RECONCILED' if not codes else ('CLOSED_EXCEPTION' if closed else 'OPEN_EXCEPTION'),
        })
    open_exceptions = [row for row in rows if row['reconciliation_status'] == 'OPEN_EXCEPTION']
    return {
        'step': '137',
        'name': 'Recovery Drill Audit, Evidence Reconciliation & Exception Closure',
        'generated_at_utc': utc_now(),
        'read_only_preview': True,
        'production_state_changed': False,
        'registry_modified': False,
        'drill_audit_modified': False,
        'drill_count': len(rows),
        'reconciled_count': sum(1 for row in rows if row['reconciliation_status'] == 'RECONCILED'),
        'open_exception_count': len(open_exceptions),
        'closed_exception_count': sum(1 for row in rows if row['reconciliation_status'] == 'CLOSED_EXCEPTION'),
        'rows': rows,
        'open_exceptions': open_exceptions,
    }


def close_reconciliation_exception(
    exception: dict[str, Any],
    *,
    operator_note: str,
    confirmation: str,
    closure_audit_path: Path = EXCEPTION_AUDIT_JSONL,
) -> dict[str, Any]:
    if confirmation != CLOSE_CONFIRMATION:
        raise PermissionError('Exact exception closure confirmation phrase is required.')
    note = operator_note.strip()
    if len(note) < 10:
        raise ValueError('Operator note must contain at least 10 characters.')
    if not exception.get('exception_id') or exception.get('reconciliation_status') != 'OPEN_EXCEPTION':
        raise ValueError('Only an open reconciliation exception can be closed.')
    event = {
        'step': '137',
        'event_type': 'EXCEPTION_CLOSED',
        'recorded_at_utc': utc_now(),
        'exception_id': exception['exception_id'],
        'drill_id': exception.get('drill_id'),
        'bundle_id': exception.get('bundle_id'),
        'exception_codes': list(exception.get('exception_codes') or []),
        'operator_note': note,
        'production_state_changed': False,
        'registry_modified': False,
        'drill_audit_modified': False,
    }
    closure_audit_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_jsonl(closure_audit_path)
    if not any(row.get('exception_id') == event['exception_id'] and row.get('event_type') == 'EXCEPTION_CLOSED' for row in existing):
        with closure_audit_path.open('a', encoding='utf-8', newline='') as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
            handle.flush(); os.fsync(handle.fileno())
    return event


def write_reconciliation_status(status: dict[str, Any]) -> None:
    summary = (
        '# Step 137 — Recovery Drill Audit, Evidence Reconciliation & Exception Closure\n\n'
        f"- Recovery drills: **{status['drill_count']}**\n"
        f"- Reconciled: **{status['reconciled_count']}**\n"
        f"- Open exceptions: **{status['open_exception_count']}**\n"
        f"- Closed exceptions: **{status['closed_exception_count']}**\n\n"
        'Preview is read-only. Exception closure appends an operator decision record only; it does not modify registry, drill audit, archives or production state.\n'
    )
    payload = dict(status)
    payload['summary_md'] = summary
    _atomic_write_text(STATUS_JSON, json.dumps(payload, ensure_ascii=False, indent=2))
    _atomic_write_text(SUMMARY_MD, summary)
