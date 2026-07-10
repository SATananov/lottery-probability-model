from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v129_controlled_production_activation_engine import (
    build_preflight,
    execute_one_time_activation,
    issue_one_time_activation_token,
    run_dry_run,
    validate_one_time_token,
)


def fixture_detection(status: str = 'update_available') -> dict:
    return {
        'status': status,
        'validation_passed': True,
        'draw_difference': 1,
        'official_latest_draw': {'draw_key': '2026-54', 'year': 2026, 'draw_no': 54, 'numbers': [1, 2, 3, 4, 5, 6]},
        'local_latest_draw': {'draw_key': '2026-53', 'year': 2026, 'draw_no': 53},
    }


def main() -> int:
    cfg = {
        'production_locked': False,
        'operator_consent_required': False,
        'operator_consent_granted': False,
        'operator_consent_phrase_hash': '',
        'consent_granted_at_utc': '',
        'consent_valid_hours': 24,
        'max_retry_attempts': 3,
        'retry_backoff_seconds': 0,
        'retryable_statuses': ['failed'],
        'block_same_draw_reapply': True,
    }
    preflight = build_preflight(detection_report=fixture_detection(), config=cfg, checkpoint={})
    assert preflight['ready'], preflight
    dry = run_dry_run(detection_report=fixture_detection(), config=cfg, checkpoint={}, write_outputs=False)
    assert dry['status'] == 'dry_run_ready' and not dry['production_data_changed'], dry

    with tempfile.TemporaryDirectory(prefix='step129_verify_') as tmp:
        token_path = Path(tmp) / 'token.json'
        token = issue_one_time_activation_token(preflight, token_path=token_path)
        valid, _ = validate_one_time_token(token, '2026-54', token_path=token_path)
        assert valid

        def runner(**kwargs):
            return {'status': 'completed', 'automation_report': {'status': 'draw_applied'}}

        result = execute_one_time_activation(
            token,
            detection_report=fixture_detection(),
            config=cfg,
            checkpoint={},
            runner=runner,
            token_path=token_path,
            write_outputs=False,
        )
        assert result['status'] == 'completed' and result['token_consumed'], result
        valid2, _ = validate_one_time_token(token, '2026-54', token_path=token_path)
        assert not valid2

    blocked = build_preflight(detection_report=fixture_detection('up_to_date'), config=cfg, checkpoint={})
    assert not blocked['ready']
    print('STEP_129_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
