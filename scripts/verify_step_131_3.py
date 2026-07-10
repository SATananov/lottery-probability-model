from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw
from src.v131_production_operations_dashboard_engine import build_operations_snapshot


def main() -> int:
    for relative in (
        'src/v123_bst_official_draw_detection_engine.py',
        'src/v131_production_operations_dashboard_engine.py',
        'src/v131_production_operations_dashboard_section.py',
        'scripts/verify_step_131_3.py',
    ):
        py_compile.compile(str(ROOT / relative), doraise=True)

    network_failure = detect_latest_official_draw(
        write_outputs=False,
        index_fetcher=lambda timeout: (_ for _ in ()).throw(OSError('dns unavailable')),
    )
    assert network_failure['status'] == 'official_unavailable'
    assert network_failure['failure_stage'] == 'index_fetch'
    assert network_failure['error_type'] == 'OSError'
    assert network_failure['connectivity']['index_fetch_succeeded'] is False

    parser_failure = detect_latest_official_draw(
        write_outputs=False,
        index_fetcher=lambda timeout: '<html><body>maintenance</body></html>',
    )
    assert parser_failure['failure_stage'] == 'index_parse'
    assert parser_failure['connectivity']['index_fetch_succeeded'] is True
    assert len(parser_failure['source_diagnostics']['html_sha256']) == 64

    mocked = {
        'status': 'official_unavailable',
        'message': 'mock parser failure',
        'error_type': 'RuntimeError',
        'failure_stage': 'index_parse',
        'connectivity': {'index_fetch_succeeded': True, 'detail_fetch_succeeded': False},
        'source_diagnostics': {'candidate_count': 0, 'html_sha256': 'a' * 64},
        'local_latest_draw': {'year': 2026, 'draw_number': 53, 'draw_key': '2026-53'},
        'official_latest_draw': {},
    }
    with patch('src.v131_production_operations_dashboard_engine.detect_latest_official_draw', return_value=mocked):
        dashboard = build_operations_snapshot(live_bst_check=True, write_outputs=False)
    assert dashboard['bst']['failure_stage'] == 'index_parse'
    assert dashboard['bst']['connectivity']['index_fetch_succeeded'] is True
    assert dashboard['bst']['source_diagnostics']['candidate_count'] == 0
    assert dashboard['heavy_ml_retraining_performed'] is False

    print('STEP_131_3_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
