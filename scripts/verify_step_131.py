from __future__ import annotations
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v131_production_operations_dashboard_engine import build_operations_snapshot


def main() -> int:
    report = build_operations_snapshot(live_bst_check=False, write_outputs=False)
    assert report['step'] == '131'
    assert report['health'] in {'healthy', 'attention', 'critical'}
    assert 'bst' in report and 'guardrails' in report and 'freshness' in report
    assert 'activation' in report and 'recovery' in report
    assert report['heavy_ml_retraining_performed'] is False

    mocked_detection = {
        'status': 'up_to_date',
        'draw_delta': 0,
        'message': 'mocked live detection',
        'local_latest_draw': {'year': 2026, 'draw_number': 53, 'draw_key': '2026-53'},
        'official_latest_draw': {'year': 2026, 'draw_number': 53, 'draw_key': '2026-53'},
    }
    with patch(
        'src.v131_production_operations_dashboard_engine.detect_latest_official_draw',
        return_value=mocked_detection,
    ) as detector:
        live = build_operations_snapshot(live_bst_check=True, timeout_seconds=30, write_outputs=False)
        detector.assert_called_once_with(timeout=30, write_outputs=False)
        assert live['bst']['status'] == 'up_to_date'
        assert live['bst']['official_draw_key'] == '2026-53'

    print('STEP_131_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
