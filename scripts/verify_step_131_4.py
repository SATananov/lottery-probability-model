from __future__ import annotations

import py_compile
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v131_production_operations_dashboard_engine import build_operations_snapshot


def main() -> int:
    for relative in (
        'src/v131_production_operations_dashboard_engine.py',
        'src/v131_production_operations_dashboard_section.py',
        'scripts/verify_step_131_4.py',
    ):
        py_compile.compile(str(ROOT / relative), doraise=True)

    with patch('src.v131_production_operations_dashboard_engine._read_json', return_value={}):
        idle = build_operations_snapshot(live_bst_check=False, write_outputs=False)
    assert idle['bst']['operational_state']['code'] == 'not_checked'
    assert idle['bst']['operational_state']['label_bg'] == 'Не е проверено'

    failure = {
        'status': 'official_unavailable',
        'message': 'dns unavailable',
        'error_type': 'OSError',
        'failure_stage': 'index_fetch',
        'connectivity': {'index_fetch_succeeded': False, 'detail_fetch_succeeded': False},
        'source_diagnostics': {},
        'local_latest_draw': {'year': 2026, 'draw_number': 53, 'draw_key': '2026-53'},
        'official_latest_draw': {},
    }
    with patch('src.v131_production_operations_dashboard_engine.detect_latest_official_draw', return_value=failure):
        failed = build_operations_snapshot(live_bst_check=True, write_outputs=False)
    incident = failed['bst']['operational_state']
    assert incident['code'] == 'BST_INDEX_UNREACHABLE'
    assert incident['severity'] == 'warning'
    assert 'DNS' in incident['operator_action_bg']
    assert failed['heavy_ml_retraining_performed'] is False

    online = dict(failure)
    online.update({
        'status': 'synced',
        'failure_stage': None,
        'official_latest_draw': {'year': 2026, 'draw_number': 53, 'draw_key': '2026-53'},
    })
    with patch('src.v131_production_operations_dashboard_engine.detect_latest_official_draw', return_value=online):
        healthy_bst = build_operations_snapshot(live_bst_check=True, write_outputs=False)
    assert healthy_bst['bst']['operational_state']['code'] == 'online'
    assert healthy_bst['bst']['operational_state']['severity'] == 'success'

    print('STEP_131_4_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
