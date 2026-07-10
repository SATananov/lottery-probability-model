from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v128_production_auto_apply_guardrails_engine import (
    CONSENT_PHRASE, DEFAULT_CONFIG, _hash_phrase, guardrail_readiness,
    run_guarded_production_automation,
)


def main() -> int:
    locked = run_guarded_production_automation(config=DEFAULT_CONFIG, checkpoint={}, runner=lambda **_: {}, write_outputs=False)
    assert locked['status'] == 'blocked'

    cfg = dict(DEFAULT_CONFIG)
    cfg.update({
        'production_locked': False,
        'operator_consent_granted': True,
        'operator_consent_phrase_hash': _hash_phrase(CONSENT_PHRASE),
        'consent_granted_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'retry_backoff_seconds': 0,
    })
    calls = {'n': 0}
    def flaky(**kwargs):
        calls['n'] += 1
        if calls['n'] < 2:
            return {'status': 'check_failed', 'detection': {}, 'ingestion': {}, 'downstream_refresh': {}}
        return {
            'status': 'completed',
            'detection': {'official_latest_draw': {'draw_key': '2026-54'}},
            'ingestion': {'status': 'inserted'},
            'downstream_refresh': {'status': 'completed'},
        }
    ok = run_guarded_production_automation(config=cfg, checkpoint={}, runner=flaky, sleep_fn=lambda _: None, write_outputs=False)
    assert ok['status'] == 'completed', ok
    assert ok['attempt_count'] == 2, ok
    assert ok['checkpoint_updated'] is True, ok

    dup = run_guarded_production_automation(
        config=cfg,
        checkpoint={'last_success_draw_key': '2026-54'},
        runner=lambda **_: {'status': 'completed', 'detection': {'official_latest_draw': {'draw_key': '2026-54'}}, 'ingestion': {'status': 'inserted'}, 'downstream_refresh': {'status': 'completed'}},
        sleep_fn=lambda _: None,
        write_outputs=False,
    )
    assert dup['status'] == 'duplicate_checkpoint_blocked', dup
    assert dup['same_draw_reapply_blocked'] is True, dup
    assert guardrail_readiness(cfg, {})['ready'] is True
    assert ok['heavy_ml_retraining_performed'] is False
    print('STEP_128_VERIFY_OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
