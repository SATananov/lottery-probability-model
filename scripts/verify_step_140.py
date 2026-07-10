from __future__ import annotations

import tempfile
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v140_production_operations_module_closure_engine import (
    REQUIRED_COMPONENTS,
    build_module_closure_status,
    module_closure_markdown,
)


def main() -> None:
    status = build_module_closure_status(
        root=ROOT,
        now=datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert status['module_state'] == 'MODULE_CLOSED'
    assert status['closure_ready'] is True
    assert status['missing_component_count'] == 0
    assert status['present_component_count'] == status['required_component_count']
    assert status['read_only'] is True
    assert status['production_state_changed'] is False
    assert status['evidence_archives_modified'] is False
    assert status['registry_modified'] is False
    assert status['audit_logs_modified'] is False
    assert status['automatic_restore_performed'] is False
    assert status['downstream_refresh_started'] is False
    assert status['ml_retraining_started'] is False
    assert 'Closure state: **MODULE_CLOSED**' in module_closure_markdown(status)

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for relative_paths in REQUIRED_COMPONENTS.values():
            for relative_path in relative_paths:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('placeholder', encoding='utf-8')
        missing_target = root / 'src/v139_recovery_exception_management_summary_engine.py'
        missing_target.unlink()
        blocked = build_module_closure_status(root=root)
        assert blocked['module_state'] == 'CLOSURE_BLOCKED'
        assert blocked['closure_ready'] is False
        assert 'src/v139_recovery_exception_management_summary_engine.py' in blocked['missing_components']

    print('STEP_140_VERIFY_OK')


if __name__ == '__main__':
    main()
