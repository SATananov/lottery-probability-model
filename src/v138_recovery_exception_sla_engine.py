from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.v137_recovery_drill_audit_reconciliation_engine import (
    EXCEPTION_AUDIT_JSONL,
    build_reconciliation_status,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v138_recovery_exception_sla_status.json'
SUMMARY_MD = ROOT / 'reports' / 'v138_recovery_exception_sla_summary.md'
FOLLOW_UP_AUDIT_JSONL = ROOT / 'reports' / 'v138_recovery_exception_follow_up_audit.jsonl'
ACK_CONFIRMATION = 'ACKNOWLEDGE RECOVERY EXCEPTION ESCALATION'

CRITICAL_CODES = {'PRODUCTION_STATE_CHANGED', 'AUTOMATIC_RESTORE_FLAG_UNSAFE'}
HIGH_CODES = {'STAGING_SHA_MISMATCH', 'REGISTRY_SHA_MISMATCH', 'INTEGRITY_NOT_VERIFIED', 'DRILL_NOT_PASSED'}
MEDIUM_CODES = {'REGISTRY_RECORD_MISSING', 'LATEST_REGISTRY_NOT_VERIFIED'}
SLA_HOURS = {'critical': 4, 'high': 24, 'medium': 72, 'low': 168}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _parse_utc(value: Any) -> datetime:
    text = str(value or '').strip()
    if not text:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def _priority(codes: list[str]) -> str:
    values = set(codes)
    if values & CRITICAL_CODES:
        return 'critical'
    if values & HIGH_CODES:
        return 'high'
    if values & MEDIUM_CODES:
        return 'medium'
    return 'low'


def _latest_follow_up_by_exception(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in _load_jsonl(path):
        exception_id = str(event.get('exception_id') or '').strip()
        if exception_id:
            latest[exception_id] = event
    return latest


def build_exception_follow_up_queue(
    *,
    now: datetime | None = None,
    reconciliation_status: dict[str, Any] | None = None,
    follow_up_audit_path: Path = FOLLOW_UP_AUDIT_JSONL,
) -> dict[str, Any]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    reconciliation = reconciliation_status or build_reconciliation_status()
    follow_up = _latest_follow_up_by_exception(follow_up_audit_path)
    rows: list[dict[str, Any]] = []
    for exception in reconciliation.get('rows', []):
        exception_id = str(exception.get('exception_id') or '')
        if not exception_id:
            continue
        priority = _priority(list(exception.get('exception_codes') or []))
        opened_at = _parse_utc(exception.get('completed_at_utc'))
        due_at = opened_at + timedelta(hours=SLA_HOURS[priority])
        closed = exception.get('reconciliation_status') == 'CLOSED_EXCEPTION'
        remaining_seconds = int((due_at - current).total_seconds())
        if closed:
            sla_state = 'closed'
        elif remaining_seconds < 0:
            sla_state = 'overdue'
        elif remaining_seconds <= 4 * 3600:
            sla_state = 'due_soon'
        else:
            sla_state = 'open'
        latest = follow_up.get(exception_id) or {}
        rows.append({
            'exception_id': exception_id,
            'bundle_id': exception.get('bundle_id'),
            'drill_id': exception.get('drill_id'),
            'priority': priority,
            'sla_hours': SLA_HOURS[priority],
            'opened_at_utc': opened_at.isoformat(timespec='seconds'),
            'due_at_utc': due_at.isoformat(timespec='seconds'),
            'sla_state': sla_state,
            'seconds_to_due': remaining_seconds,
            'exception_codes': list(exception.get('exception_codes') or []),
            'reconciliation_status': exception.get('reconciliation_status'),
            'latest_follow_up_event': latest.get('event_type'),
            'latest_follow_up_at_utc': latest.get('recorded_at_utc'),
            'latest_operator_note': latest.get('operator_note'),
            'escalation_required': sla_state in {'overdue', 'due_soon'} and not closed,
        })
    order = {'overdue': 0, 'due_soon': 1, 'open': 2, 'closed': 3}
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    rows.sort(key=lambda row: (order[row['sla_state']], priority_order[row['priority']], row['due_at_utc']))
    open_rows = [row for row in rows if row['sla_state'] != 'closed']
    return {
        'step': '138',
        'name': 'Recovery Exception SLA, Escalation & Operator Follow-up Queue',
        'generated_at_utc': current.isoformat(timespec='seconds'),
        'read_only_preview': True,
        'production_state_changed': False,
        'reconciliation_audit_modified': False,
        'exception_count': len(rows),
        'open_count': len(open_rows),
        'overdue_count': sum(1 for row in rows if row['sla_state'] == 'overdue'),
        'due_soon_count': sum(1 for row in rows if row['sla_state'] == 'due_soon'),
        'critical_count': sum(1 for row in open_rows if row['priority'] == 'critical'),
        'rows': rows,
        'action_queue': open_rows,
    }


def record_follow_up_event(
    queue_item: dict[str, Any],
    *,
    operator_note: str,
    confirmation: str,
    follow_up_audit_path: Path = FOLLOW_UP_AUDIT_JSONL,
) -> dict[str, Any]:
    if confirmation != ACK_CONFIRMATION:
        raise PermissionError('Exact escalation acknowledgement confirmation phrase is required.')
    note = operator_note.strip()
    if len(note) < 10:
        raise ValueError('Operator follow-up note must contain at least 10 characters.')
    if queue_item.get('sla_state') == 'closed':
        raise ValueError('Closed exceptions do not require a new escalation acknowledgement.')
    exception_id = str(queue_item.get('exception_id') or '').strip()
    if not exception_id:
        raise ValueError('Valid exception_id is required.')
    event = {
        'step': '138',
        'event_type': 'ESCALATION_ACKNOWLEDGED',
        'recorded_at_utc': utc_now(),
        'follow_up_id': 'FUP-' + hashlib.sha256(f"{exception_id}|{utc_now()}|{note}".encode('utf-8')).hexdigest()[:16].upper(),
        'exception_id': exception_id,
        'bundle_id': queue_item.get('bundle_id'),
        'drill_id': queue_item.get('drill_id'),
        'priority': queue_item.get('priority'),
        'sla_state_at_acknowledgement': queue_item.get('sla_state'),
        'due_at_utc': queue_item.get('due_at_utc'),
        'exception_codes': list(queue_item.get('exception_codes') or []),
        'operator_note': note,
        'production_state_changed': False,
        'reconciliation_audit_modified': False,
        'evidence_archives_modified': False,
    }
    follow_up_audit_path.parent.mkdir(parents=True, exist_ok=True)
    with follow_up_audit_path.open('a', encoding='utf-8', newline='') as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
        handle.flush(); os.fsync(handle.fileno())
    return event


def write_exception_follow_up_status(status: dict[str, Any]) -> None:
    summary = (
        '# Step 138 — Recovery Exception SLA, Escalation & Operator Follow-up Queue\n\n'
        f"- Exceptions tracked: **{status['exception_count']}**\n"
        f"- Open: **{status['open_count']}**\n"
        f"- Overdue: **{status['overdue_count']}**\n"
        f"- Due soon: **{status['due_soon_count']}**\n"
        f"- Critical open: **{status['critical_count']}**\n\n"
        'The queue is read-only. Acknowledgement appends a follow-up audit event only and never closes exceptions or modifies evidence archives.\n'
    )
    payload = dict(status)
    payload['summary_md'] = summary
    _atomic_write_text(STATUS_JSON, json.dumps(payload, ensure_ascii=False, indent=2))
    _atomic_write_text(SUMMARY_MD, summary)
