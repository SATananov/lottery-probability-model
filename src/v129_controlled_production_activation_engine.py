from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw
from src.v128_production_auto_apply_guardrails_engine import (
    guardrail_readiness,
    load_checkpoint,
    load_config,
    run_guarded_production_automation,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v129_controlled_production_activation_status.json'
TOKEN_JSON = ROOT / 'models' / 'v129_one_time_activation_token.json'
REPORT_JSON = ROOT / 'reports' / 'v129_controlled_production_activation_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v129_controlled_production_activation_summary.md'
AUDIT_JSONL = ROOT / 'reports' / 'v129_controlled_production_activation_audit.jsonl'

DEFAULT_TOKEN_TTL_MINUTES = 15


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _parse_utc(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_outputs(report: dict[str, Any]) -> None:
    _write_json(STATUS_JSON, report)
    _write_json(REPORT_JSON, report)
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.write_text('\n'.join([
        '# Step 129 — Controlled Production Activation & Dry-Run Console', '',
        f"- Status: **{report.get('status', '')}**",
        f"- Mode: **{report.get('mode', '')}**",
        f"- Preflight ready: **{report.get('preflight_ready', False)}**",
        f"- Target draw: **{report.get('target_draw_key') or '—'}**",
        f"- Activation executed: **{report.get('activation_executed', False)}**",
        f"- One-time token consumed: **{report.get('token_consumed', False)}**",
        '- Heavy ML retraining: **No**', '',
        str(report.get('message', '')), ''
    ]), encoding='utf-8')
    AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_JSONL.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + '\n')


def build_preflight(
    *,
    detection_report: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    detection = detection_report or detect_latest_official_draw(write_outputs=False)
    cfg = config or load_config()
    cp = load_checkpoint() if checkpoint is None else checkpoint
    readiness = guardrail_readiness(cfg, cp)
    official = detection.get('official_latest_draw') or {}
    local = detection.get('local_latest_draw') or {}
    target_key = official.get('draw_key')
    local_key = local.get('draw_key')
    detection_status = detection.get('status')
    new_draw_available = detection_status == 'update_available'
    already_checkpointed = bool(target_key and cp.get('last_success_draw_key') == target_key)

    checks = {
        'official_source_available': bool(target_key),
        'official_draw_validated': bool(detection.get('validation_passed', detection_status in {'up_to_date', 'update_available'})),
        'new_draw_available': new_draw_available,
        'sequential_draw': detection.get('draw_difference') in {1, None} if new_draw_available else False,
        'production_unlocked': readiness['checks'].get('production_unlocked', False),
        'operator_consent_valid': readiness['checks'].get('operator_consent_valid', False),
        'retry_policy_valid': readiness['checks'].get('retry_policy_valid', False),
        'same_draw_protection_enabled': readiness['checks'].get('same_draw_protection_enabled', False),
        'not_already_checkpointed': not already_checkpointed,
    }
    ready = all(checks.values())
    return {
        'step': '129',
        'name': 'Controlled Production Activation & Dry-Run Console',
        'created_at_utc': utc_now(),
        'ready': ready,
        'checks': checks,
        'target_draw_key': target_key,
        'local_draw_key': local_key,
        'detection_status': detection_status,
        'detection': detection,
        'guardrail_readiness': readiness,
        'last_success_checkpoint': cp,
        'operator_summary': (
            f"Target {target_key or '—'}; local {local_key or '—'}; "
            f"detection {detection_status or 'unknown'}; production "
            f"{'UNLOCKED' if checks['production_unlocked'] else 'LOCKED'}; "
            f"consent {'VALID' if checks['operator_consent_valid'] else 'MISSING/EXPIRED'}."
        ),
    }


def run_dry_run(
    *,
    detection_report: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    preflight = build_preflight(detection_report=detection_report, config=config, checkpoint=checkpoint)
    report = {
        'step': '129',
        'name': 'Controlled Production Activation & Dry-Run Console',
        'mode': 'dry_run',
        'started_at_utc': utc_now(),
        'finished_at_utc': utc_now(),
        'status': 'dry_run_ready' if preflight['ready'] else 'dry_run_blocked',
        'message': 'Dry-run preflight е готов за еднократно активиране.' if preflight['ready'] else 'Dry-run preflight е блокиран; production данните не са променени.',
        'preflight_ready': preflight['ready'],
        'target_draw_key': preflight['target_draw_key'],
        'preflight': preflight,
        'activation_executed': False,
        'token_consumed': False,
        'production_data_changed': False,
        'heavy_ml_retraining_performed': False,
    }
    if write_outputs:
        _write_outputs(report)
    return report


def issue_one_time_activation_token(
    preflight: dict[str, Any],
    *,
    ttl_minutes: int = DEFAULT_TOKEN_TTL_MINUTES,
    token_path: Path = TOKEN_JSON,
) -> str:
    if not preflight.get('ready'):
        raise ValueError('Preflight не е готов; activation token не може да бъде издаден.')
    draw_key = preflight.get('target_draw_key')
    if not draw_key:
        raise ValueError('Липсва конкретен target draw key.')
    token = secrets.token_urlsafe(24)
    now = datetime.now(timezone.utc)
    payload = {
        'step': '129',
        'token_hash': _hash_token(token),
        'target_draw_key': draw_key,
        'issued_at_utc': now.isoformat(timespec='seconds'),
        'expires_at_utc': (now + timedelta(minutes=max(1, min(60, ttl_minutes)))).isoformat(timespec='seconds'),
        'consumed': False,
        'consumed_at_utc': '',
    }
    _write_json(token_path, payload)
    return token


def validate_one_time_token(token: str, target_draw_key: str, *, token_path: Path = TOKEN_JSON) -> tuple[bool, str]:
    payload = _read_json(token_path)
    if not payload:
        return False, 'Липсва издаден activation token.'
    if payload.get('consumed'):
        return False, 'Activation token вече е използван.'
    expires = _parse_utc(payload.get('expires_at_utc'))
    if expires is None or datetime.now(timezone.utc) > expires:
        return False, 'Activation token е изтекъл.'
    if payload.get('target_draw_key') != target_draw_key:
        return False, 'Activation token е издаден за друг тираж.'
    if payload.get('token_hash') != _hash_token(token):
        return False, 'Activation token не съвпада.'
    return True, 'valid'


def _consume_token(*, token_path: Path = TOKEN_JSON) -> None:
    payload = _read_json(token_path)
    payload['consumed'] = True
    payload['consumed_at_utc'] = utc_now()
    _write_json(token_path, payload)


def execute_one_time_activation(
    token: str,
    *,
    detection_report: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
    runner: Callable[..., dict[str, Any]] | None = None,
    token_path: Path = TOKEN_JSON,
    write_outputs: bool = True,
) -> dict[str, Any]:
    preflight = build_preflight(detection_report=detection_report, config=config, checkpoint=checkpoint)
    target = preflight.get('target_draw_key') or ''
    valid, reason = validate_one_time_token(token, target, token_path=token_path)
    report: dict[str, Any] = {
        'step': '129',
        'name': 'Controlled Production Activation & Dry-Run Console',
        'mode': 'one_time_activation',
        'started_at_utc': utc_now(),
        'finished_at_utc': utc_now(),
        'status': 'blocked',
        'message': '',
        'preflight_ready': preflight.get('ready', False),
        'target_draw_key': target or None,
        'preflight': preflight,
        'activation_executed': False,
        'token_consumed': False,
        'production_data_changed': False,
        'heavy_ml_retraining_performed': False,
        'guarded_report': {},
    }
    if not preflight.get('ready'):
        report['message'] = 'Финалният preflight вече не е готов. Activation е блокиран.'
    elif not valid:
        report['message'] = reason
    else:
        execute = runner or run_guarded_production_automation
        guarded = execute(trigger='step129_one_time_activation', force_check=True)
        report['guarded_report'] = guarded
        success = guarded.get('status') == 'completed'
        report['activation_executed'] = True
        report['production_data_changed'] = success and (guarded.get('automation_report') or {}).get('status') in {'draw_applied', 'completed'}
        report['status'] = 'completed' if success else 'failed'
        report['message'] = 'Еднократното production активиране завърши успешно.' if success else 'Guarded production изпълнението не завърши успешно.'
        _consume_token(token_path=token_path)
        report['token_consumed'] = True
    report['finished_at_utc'] = utc_now()
    if write_outputs:
        _write_outputs(report)
    return report
