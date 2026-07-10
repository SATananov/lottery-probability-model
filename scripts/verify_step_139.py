from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v139_recovery_exception_management_summary_engine import (
    build_recovery_exception_management_summary,
    management_summary_csv,
    management_summary_markdown,
)


def main() -> None:
    reconciliation = {
        'drill_count': 4,
        'reconciled_count': 1,
        'open_exception_count': 2,
        'closed_exception_count': 1,
        'rows': [],
    }
    queue = {
        'overdue_count': 1,
        'due_soon_count': 1,
        'critical_count': 1,
        'rows': [
            {'exception_id': 'EXC-CRIT', 'bundle_id': 'INC-1', 'priority': 'critical', 'sla_state': 'overdue'},
            {'exception_id': 'EXC-HIGH', 'bundle_id': 'INC-2', 'priority': 'high', 'sla_state': 'due_soon'},
        ],
        'action_queue': [
            {'exception_id': 'EXC-CRIT', 'bundle_id': 'INC-1', 'priority': 'critical', 'sla_state': 'overdue', 'due_at_utc': '2026-07-10T04:00:00+00:00', 'exception_codes': ['PRODUCTION_STATE_CHANGED']},
            {'exception_id': 'EXC-HIGH', 'bundle_id': 'INC-2', 'priority': 'high', 'sla_state': 'due_soon', 'due_at_utc': '2026-07-10T12:00:00+00:00', 'exception_codes': ['STAGING_SHA_MISMATCH']},
        ],
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        drill_path = Path(temp_dir) / 'drills.jsonl'
        drills = [
            {'drill_id': 'D1', 'bundle_id': 'INC-1', 'completed_at_utc': '2026-07-10T01:00:00+00:00', 'drill_verdict': 'failed', 'integrity_verdict': 'invalid', 'production_state_changed': False, 'automatic_production_restore_performed': False},
            {'drill_id': 'D2', 'bundle_id': 'INC-2', 'completed_at_utc': '2026-07-09T01:00:00+00:00', 'drill_verdict': 'passed', 'integrity_verdict': 'verified', 'production_state_changed': False, 'automatic_production_restore_performed': False},
        ]
        drill_path.write_text('\n'.join(json.dumps(row) for row in drills) + '\n', encoding='utf-8')
        before = drill_path.read_bytes()
        status = build_recovery_exception_management_summary(
            reconciliation_status=reconciliation,
            queue_status=queue,
            drill_audit_path=drill_path,
            now=datetime(2026, 7, 10, 6, 0, 0, tzinfo=timezone.utc),
        )
        assert status['management_health'] == 'RED'
        assert status['open_exception_count'] == 2
        assert status['closed_exception_count'] == 1
        assert status['overdue_exception_count'] == 1
        assert status['critical_open_count'] == 1
        assert status['latest_failed_drill_count'] == 1
        assert status['attention_required_count'] == 3
        assert status['production_state_changed'] is False
        assert status['registry_modified'] is False
        assert status['reconciliation_audit_modified'] is False
        assert drill_path.read_bytes() == before
        assert 'Management health: **RED**' in management_summary_markdown(status)
        csv_text = management_summary_csv(status)
        assert 'EXC-CRIT' in csv_text and 'DRILL_NOT_PASSED' in csv_text

        green = build_recovery_exception_management_summary(
            reconciliation_status={'drill_count': 1, 'reconciled_count': 1, 'open_exception_count': 0, 'closed_exception_count': 0, 'rows': []},
            queue_status={'overdue_count': 0, 'due_soon_count': 0, 'critical_count': 0, 'rows': [], 'action_queue': []},
            drill_audit_path=Path(temp_dir) / 'missing.jsonl',
            now=datetime(2026, 7, 10, 6, 0, 0, tzinfo=timezone.utc),
        )
        assert green['management_health'] == 'GREEN'
        assert green['attention_required_count'] == 0
    print('STEP_139_VERIFY_OK')


if __name__ == '__main__':
    main()
