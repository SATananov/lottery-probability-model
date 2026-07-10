from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v136_incident_evidence_recovery_drill_engine import AUDIT_JSONL as DRILL_AUDIT_JSONL
from src.v137_recovery_drill_audit_reconciliation_engine import build_reconciliation_status
from src.v138_recovery_exception_sla_engine import build_exception_follow_up_queue

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v139_recovery_exception_management_summary_status.json'
SUMMARY_MD = ROOT / 'reports' / 'v139_recovery_exception_management_summary.md'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


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


def _latest_drills(drill_audit_path: Path, limit: int = 10) -> list[dict[str, Any]]:
    rows = _load_jsonl(drill_audit_path)
    rows.sort(key=lambda row: str(row.get('completed_at_utc') or ''), reverse=True)
    return [
        {
            'drill_id': row.get('drill_id'),
            'bundle_id': row.get('bundle_id'),
            'completed_at_utc': row.get('completed_at_utc'),
            'drill_verdict': row.get('drill_verdict'),
            'integrity_verdict': row.get('integrity_verdict'),
            'production_state_changed': row.get('production_state_changed'),
            'automatic_production_restore_performed': row.get('automatic_production_restore_performed'),
        }
        for row in rows[:limit]
    ]


def _management_health(*, overdue: int, critical: int, due_soon: int, failed_drills: int, open_count: int) -> str:
    if overdue > 0 or critical > 0 or failed_drills > 0:
        return 'RED'
    if due_soon > 0 or open_count > 0:
        return 'AMBER'
    return 'GREEN'


def _attention_actions(queue: dict[str, Any], failed_drills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for row in queue.get('action_queue', []):
        if row.get('sla_state') not in {'overdue', 'due_soon'} and row.get('priority') != 'critical':
            continue
        if row.get('priority') == 'critical':
            action = 'Immediate operator review and Step 137 exception resolution are required.'
        elif row.get('sla_state') == 'overdue':
            action = 'SLA is overdue; escalate, document follow-up, and resolve through Step 137.'
        else:
            action = 'SLA is approaching; assign an operator and record follow-up before the due time.'
        actions.append({
            'type': 'RECOVERY_EXCEPTION',
            'priority': row.get('priority'),
            'sla_state': row.get('sla_state'),
            'exception_id': row.get('exception_id'),
            'bundle_id': row.get('bundle_id'),
            'due_at_utc': row.get('due_at_utc'),
            'exception_codes': list(row.get('exception_codes') or []),
            'recommended_action': action,
        })
    for drill in failed_drills:
        actions.append({
            'type': 'FAILED_RECOVERY_DRILL',
            'priority': 'high',
            'sla_state': 'review_required',
            'exception_id': None,
            'bundle_id': drill.get('bundle_id'),
            'due_at_utc': None,
            'exception_codes': ['DRILL_NOT_PASSED'],
            'recommended_action': 'Review Step 136 drill evidence and reconcile the failure through Step 137.',
        })
    order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    state_order = {'overdue': 0, 'due_soon': 1, 'review_required': 2, 'open': 3}
    actions.sort(key=lambda row: (order.get(str(row.get('priority')), 9), state_order.get(str(row.get('sla_state')), 9), str(row.get('due_at_utc') or '')))
    return actions


def build_recovery_exception_management_summary(
    *,
    reconciliation_status: dict[str, Any] | None = None,
    queue_status: dict[str, Any] | None = None,
    drill_audit_path: Path = DRILL_AUDIT_JSONL,
    now: datetime | None = None,
    latest_drill_limit: int = 10,
) -> dict[str, Any]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    reconciliation = reconciliation_status or build_reconciliation_status()
    queue = queue_status or build_exception_follow_up_queue(now=current, reconciliation_status=reconciliation)
    latest_drills = _latest_drills(drill_audit_path, latest_drill_limit)
    failed_drills = [row for row in latest_drills if str(row.get('drill_verdict') or '').lower() != 'passed']
    passed_drills = [row for row in latest_drills if str(row.get('drill_verdict') or '').lower() == 'passed']
    open_count = int(reconciliation.get('open_exception_count') or 0)
    closed_count = int(reconciliation.get('closed_exception_count') or 0)
    overdue_count = int(queue.get('overdue_count') or 0)
    due_soon_count = int(queue.get('due_soon_count') or 0)
    critical_count = int(queue.get('critical_count') or 0)
    health = _management_health(
        overdue=overdue_count,
        critical=critical_count,
        due_soon=due_soon_count,
        failed_drills=len(failed_drills),
        open_count=open_count,
    )
    actions = _attention_actions(queue, failed_drills)
    return {
        'step': '139',
        'name': 'Recovery Exception Reporting & Management Summary',
        'generated_at_utc': current.isoformat(timespec='seconds'),
        'read_only': True,
        'management_health': health,
        'production_state_changed': False,
        'evidence_archives_modified': False,
        'registry_modified': False,
        'reconciliation_audit_modified': False,
        'follow_up_audit_modified': False,
        'drill_count': int(reconciliation.get('drill_count') or 0),
        'reconciled_count': int(reconciliation.get('reconciled_count') or 0),
        'open_exception_count': open_count,
        'closed_exception_count': closed_count,
        'overdue_exception_count': overdue_count,
        'due_soon_exception_count': due_soon_count,
        'critical_open_count': critical_count,
        'latest_drill_count': len(latest_drills),
        'latest_passed_drill_count': len(passed_drills),
        'latest_failed_drill_count': len(failed_drills),
        'attention_required_count': len(actions),
        'attention_required': actions,
        'latest_drills': latest_drills,
        'exception_rows': list(queue.get('rows') or []),
    }


def management_summary_markdown(status: dict[str, Any]) -> str:
    lines = [
        '# Step 139 — Recovery Exception Reporting & Management Summary',
        '',
        f"- Management health: **{status['management_health']}**",
        f"- Recovery drills: **{status['drill_count']}**",
        f"- Reconciled: **{status['reconciled_count']}**",
        f"- Open exceptions: **{status['open_exception_count']}**",
        f"- Closed exceptions: **{status['closed_exception_count']}**",
        f"- SLA overdue: **{status['overdue_exception_count']}**",
        f"- Due soon: **{status['due_soon_exception_count']}**",
        f"- Critical open: **{status['critical_open_count']}**",
        f"- Latest failed drills: **{status['latest_failed_drill_count']}**",
        f"- Attention required: **{status['attention_required_count']}**",
        '',
        '## Management attention',
        '',
    ]
    if status['attention_required']:
        for item in status['attention_required']:
            identity = item.get('exception_id') or item.get('bundle_id') or 'unknown'
            lines.append(f"- **{item.get('priority', 'unknown').upper()}** `{identity}` — {item.get('recommended_action')}")
    else:
        lines.append('- No immediate management action is required.')
    lines.extend([
        '',
        'This report is read-only. It does not acknowledge, close, archive, restore or modify incident evidence.',
        '',
    ])
    return '\n'.join(lines)


def management_summary_csv(status: dict[str, Any]) -> str:
    output = io.StringIO(newline='')
    fields = ['type', 'priority', 'sla_state', 'exception_id', 'bundle_id', 'due_at_utc', 'exception_codes', 'recommended_action']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for item in status.get('attention_required', []):
        row = dict(item)
        row['exception_codes'] = '|'.join(row.get('exception_codes') or [])
        writer.writerow({field: row.get(field) for field in fields})
    return output.getvalue()


def write_recovery_exception_management_summary(status: dict[str, Any]) -> None:
    payload = dict(status)
    payload['summary_md'] = management_summary_markdown(status)
    _atomic_write_text(STATUS_JSON, json.dumps(payload, ensure_ascii=False, indent=2))
    _atomic_write_text(SUMMARY_MD, payload['summary_md'])
