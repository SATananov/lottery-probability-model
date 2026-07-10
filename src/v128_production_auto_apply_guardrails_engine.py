from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from src.v126_startup_automation_engine import load_config as load_v126_config
from src.v126_startup_automation_engine import run_startup_automation

ROOT = Path(__file__).resolve().parents[1]
CONFIG_JSON = ROOT / 'models' / 'v128_production_guardrails_config.json'
STATUS_JSON = ROOT / 'models' / 'v128_production_guardrails_status.json'
CHECKPOINT_JSON = ROOT / 'models' / 'v128_last_success_checkpoint.json'
REPORT_JSON = ROOT / 'reports' / 'v128_production_guardrails_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v128_production_guardrails_summary.md'
AUDIT_JSONL = ROOT / 'reports' / 'v128_production_guardrails_audit.jsonl'

CONSENT_PHRASE = 'РАЗРЕШАВАМ АВТОМАТИЧНО ПРИЛАГАНЕ'
DEFAULT_CONFIG: dict[str, Any] = {
    'production_locked': True,
    'operator_consent_required': True,
    'operator_consent_granted': False,
    'operator_consent_phrase_hash': '',
    'consent_granted_at_utc': '',
    'consent_valid_hours': 24,
    'max_retry_attempts': 3,
    'retry_backoff_seconds': 5,
    'retryable_statuses': ['check_failed', 'failed'],
    'block_same_draw_reapply': True,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _hash_phrase(value: str) -> str:
    return hashlib.sha256(value.strip().encode('utf-8')).hexdigest()


def _parse_utc(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return None


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    result = dict(DEFAULT_CONFIG)
    result.update(config or {})
    result['production_locked'] = bool(result.get('production_locked', True))
    result['operator_consent_required'] = bool(result.get('operator_consent_required', True))
    result['operator_consent_granted'] = bool(result.get('operator_consent_granted', False))
    result['consent_valid_hours'] = max(1, min(168, int(result.get('consent_valid_hours', 24))))
    result['max_retry_attempts'] = max(1, min(5, int(result.get('max_retry_attempts', 3))))
    result['retry_backoff_seconds'] = max(0, min(300, int(result.get('retry_backoff_seconds', 5))))
    result['block_same_draw_reapply'] = bool(result.get('block_same_draw_reapply', True))
    statuses = result.get('retryable_statuses') or ['check_failed', 'failed']
    result['retryable_statuses'] = [str(x) for x in statuses]
    return result


def load_config(path: Path = CONFIG_JSON) -> dict[str, Any]:
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return normalize_config(data if isinstance(data, dict) else {})
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_CONFIG)


def save_config(config: dict[str, Any], path: Path = CONFIG_JSON) -> dict[str, Any]:
    normalized = normalize_config(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return normalized


def grant_operator_consent(phrase: str, *, config_path: Path = CONFIG_JSON) -> dict[str, Any]:
    config = load_config(config_path)
    if phrase.strip() != CONSENT_PHRASE:
        raise ValueError('Фразата за операторско съгласие не съвпада.')
    config.update({
        'operator_consent_granted': True,
        'operator_consent_phrase_hash': _hash_phrase(phrase),
        'consent_granted_at_utc': utc_now(),
    })
    return save_config(config, config_path)


def revoke_operator_consent(*, config_path: Path = CONFIG_JSON) -> dict[str, Any]:
    config = load_config(config_path)
    config.update({
        'operator_consent_granted': False,
        'operator_consent_phrase_hash': '',
        'consent_granted_at_utc': '',
        'production_locked': True,
    })
    return save_config(config, config_path)


def consent_is_valid(config: dict[str, Any], now: datetime | None = None) -> bool:
    if not config.get('operator_consent_required', True):
        return True
    if not config.get('operator_consent_granted'):
        return False
    if config.get('operator_consent_phrase_hash') != _hash_phrase(CONSENT_PHRASE):
        return False
    granted = _parse_utc(config.get('consent_granted_at_utc'))
    if granted is None:
        return False
    return (now or datetime.now(timezone.utc)) <= granted + timedelta(hours=int(config['consent_valid_hours']))


def load_checkpoint(path: Path = CHECKPOINT_JSON) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_checkpoint(report: dict[str, Any], path: Path = CHECKPOINT_JSON) -> dict[str, Any]:
    detection = report.get('detection') or {}
    official = detection.get('official_latest_draw') or {}
    draw_key = official.get('draw_key')
    checkpoint = {
        'step': '128',
        'last_success_at_utc': utc_now(),
        'last_success_draw_key': draw_key,
        'automation_status': report.get('status'),
        'ingestion_status': (report.get('ingestion') or {}).get('status'),
        'downstream_status': (report.get('downstream_refresh') or {}).get('status'),
        'heavy_ml_retraining_performed': False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return checkpoint


def guardrail_readiness(config: dict[str, Any], checkpoint: dict[str, Any] | None = None) -> dict[str, Any]:
    checks = {
        'production_unlocked': not config.get('production_locked', True),
        'operator_consent_valid': consent_is_valid(config),
        'retry_policy_valid': 1 <= int(config.get('max_retry_attempts', 0)) <= 5,
        'same_draw_protection_enabled': bool(config.get('block_same_draw_reapply', True)),
        'checkpoint_layer_available': checkpoint is not None,
    }
    return {'ready': all(checks.values()), 'checks': checks}


def _write_outputs(report: dict[str, Any]) -> None:
    for path in (STATUS_JSON, REPORT_JSON, SUMMARY_MD, AUDIT_JSONL):
        path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    STATUS_JSON.write_text(payload, encoding='utf-8')
    REPORT_JSON.write_text(payload, encoding='utf-8')
    SUMMARY_MD.write_text('\n'.join([
        '# Step 128 — Production Auto-Apply Readiness & Guardrails', '',
        f"- Status: **{report.get('status', '')}**",
        f"- Production locked: **{report.get('production_locked', True)}**",
        f"- Consent valid: **{report.get('consent_valid', False)}**",
        f"- Attempts: **{report.get('attempt_count', 0)}**",
        f"- Same-draw block: **{report.get('same_draw_reapply_blocked', False)}**",
        f"- Last-success checkpoint updated: **{report.get('checkpoint_updated', False)}**",
        '- Heavy ML retraining: **No**', '', str(report.get('message', '')), ''
    ]), encoding='utf-8')
    with AUDIT_JSONL.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + '\n')


def run_guarded_production_automation(
    *,
    trigger: str = 'operator_run',
    force_check: bool = True,
    config: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
    runner: Callable[..., dict[str, Any]] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    write_outputs: bool = True,
) -> dict[str, Any]:
    cfg = normalize_config(config or load_config())
    cp = load_checkpoint() if checkpoint is None else dict(checkpoint)
    started = utc_now()
    result: dict[str, Any] = {
        'step': '128', 'name': 'Production Auto-Apply Readiness & Guardrails',
        'trigger': trigger, 'started_at_utc': started, 'finished_at_utc': started,
        'status': 'blocked', 'message': '', 'production_locked': cfg['production_locked'],
        'consent_valid': consent_is_valid(cfg), 'attempt_count': 0, 'attempts': [],
        'same_draw_reapply_blocked': False, 'checkpoint_updated': False,
        'last_success_checkpoint': cp, 'automation_report': {},
        'heavy_ml_retraining_performed': False,
    }

    if cfg['production_locked']:
        result['message'] = 'Production lock е включен. Автоматичното прилагане е блокирано.'
        if write_outputs: _write_outputs(result)
        return result
    if not result['consent_valid']:
        result['message'] = 'Липсва валидно изрично операторско съгласие.'
        if write_outputs: _write_outputs(result)
        return result

    execute = runner or run_startup_automation
    v126_cfg = dict(load_v126_config())
    v126_cfg.update({'auto_check_enabled': True, 'auto_apply_enabled': True, 'auto_refresh_enabled': True})

    for attempt in range(1, cfg['max_retry_attempts'] + 1):
        report = execute(trigger=trigger, force_check=force_check, config=v126_cfg, write_outputs=True)
        result['attempt_count'] = attempt
        result['automation_report'] = report
        result['attempts'].append({'attempt': attempt, 'status': report.get('status'), 'finished_at_utc': utc_now()})
        detection = report.get('detection') or {}
        official = detection.get('official_latest_draw') or {}
        draw_key = official.get('draw_key')
        last_key = cp.get('last_success_draw_key')

        if cfg['block_same_draw_reapply'] and draw_key and last_key == draw_key and report.get('status') in {'update_available', 'draw_applied', 'completed'}:
            result.update(status='duplicate_checkpoint_blocked', same_draw_reapply_blocked=True,
                          message=f'Тираж {draw_key} вече присъства в last-success checkpoint. Повторното прилагане е блокирано.')
            break

        if report.get('status') in {'up_to_date', 'completed', 'draw_applied'}:
            result.update(status='completed', message='Guarded production изпълнението завърши успешно.')
            if write_outputs:
                result['last_success_checkpoint'] = save_checkpoint(report)
            else:
                detection = report.get('detection') or {}
                official = detection.get('official_latest_draw') or {}
                result['last_success_checkpoint'] = {
                    'step': '128', 'last_success_at_utc': utc_now(),
                    'last_success_draw_key': official.get('draw_key'),
                    'automation_status': report.get('status'),
                    'ingestion_status': (report.get('ingestion') or {}).get('status'),
                    'downstream_status': (report.get('downstream_refresh') or {}).get('status'),
                    'heavy_ml_retraining_performed': False,
                }
            result['checkpoint_updated'] = True
            break

        if report.get('status') not in cfg['retryable_statuses'] or attempt >= cfg['max_retry_attempts']:
            result.update(status='failed', message='Guarded production изпълнението не завърши успешно; retry policy е изчерпана или статусът не е retryable.')
            break
        sleep_fn(cfg['retry_backoff_seconds'] * attempt)

    result['finished_at_utc'] = utc_now()
    if write_outputs: _write_outputs(result)
    return result
