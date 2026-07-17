from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v122_unified_official_draw_freshness_engine import build_freshness_report
from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw, load_detection_report
from src.v128_production_auto_apply_guardrails_engine import consent_is_valid, load_checkpoint, load_config
from src.v130_production_activation_audit_recovery_engine import checkpoint_inspector, list_activation_history, list_ingestion_backups

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v131_production_operations_dashboard_status.json'
REPORT_JSON = ROOT / 'reports' / 'v131_production_operations_dashboard_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v131_production_operations_dashboard_summary.md'
TOKEN_JSON = ROOT / 'models' / 'v129_one_time_activation_token.json'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _draw_key(draw: dict[str, Any] | None) -> str:
    draw = draw or {}
    if draw.get('draw_key'):
        return str(draw['draw_key'])
    year = draw.get('year') or draw.get('draw_year')
    number = draw.get('draw_number')
    return f'{year}-{number}' if year and number else '—'


def _bst_operational_state(*, live_bst_check: bool, detection_status: str, bst_available: bool, failure_stage: str | None) -> dict[str, Any]:
    if not live_bst_check and detection_status in {'not_checked', ''}:
        return {
            'code': 'not_checked',
            'label_bg': 'Не е проверено',
            'severity': 'info',
            'operator_action_bg': 'Натисни „Обнови dashboard с live БСТ проверка“, когато е нужна актуална външна проверка.',
            'retry_safe': True,
        }
    if bst_available:
        return {
            'code': 'online',
            'label_bg': 'Достъпно',
            'severity': 'success',
            'operator_action_bg': 'Не е необходимо действие. Прегледай разликата между официалния и локалния тираж.',
            'retry_safe': True,
        }

    guidance = {
        'index_fetch': (
            'BST_INDEX_UNREACHABLE',
            'Официалният индекс не е достъпен',
            'Провери интернет/DNS/TLS достъпа и повтори само read-only live проверката. Не прилагай тираж ръчно само заради мрежова грешка.',
        ),
        'index_captcha': (
            'BST_INDEX_CAPTCHA_BLOCKED',
            'Официалният индекс върна CAPTCHA',
            'Не променяй parser-а. Изчакай или използвай валидирания CAPTCHA-safe manual import поток.',
        ),
        'detail_captcha': (
            'BST_DETAIL_CAPTCHA_BLOCKED',
            'Страницата на тиража върна CAPTCHA',
            'Ingestion остава блокиран fail-closed. Използвай само валидиран ръчен импорт с официален URL.',
        ),
        'index_parse': (
            'BST_INDEX_PARSE_UNRECOGNIZED',
            'Индексът е достъпен, но форматът не е разпознат',
            'Запази диагностичния SHA-256 и parser данните. Провери за промяна в HTML структурата преди промяна на parser-а.',
        ),
        'detail_fetch': (
            'BST_DETAIL_UNREACHABLE',
            'Страницата на тиража не е достъпна',
            'Повтори read-only проверката. Ако индексът работи, но detail страницата остава недостъпна, не разрешавай ingestion.',
        ),
        'detail_validation': (
            'BST_DETAIL_VALIDATION_FAILED',
            'Официалният запис не премина валидацията',
            'Прегледай извлечените полета и validation причината. Не заобикаляй fail-closed защитата.',
        ),
        'classification': (
            'BST_DRAW_CLASSIFICATION_FAILED',
            'Тиражът не може да бъде класифициран безопасно',
            'Сравни ръчно official/local draw metadata и поправи classification логиката преди ingestion.',
        ),
    }
    code, title, action = guidance.get(
        failure_stage,
        ('BST_CHECK_FAILED', 'Live БСТ проверката е неуспешна', 'Прегледай error type, message и diagnostics преди повторна проверка.'),
    )
    return {
        'code': code,
        'label_bg': 'Недостъпно',
        'severity': 'warning',
        'title_bg': title,
        'operator_action_bg': action,
        'retry_safe': True,
    }


def build_operations_snapshot(*, live_bst_check: bool = False, timeout_seconds: int = 15, write_outputs: bool = True) -> dict[str, Any]:
    freshness = build_freshness_report(write_outputs=False)
    detection = detect_latest_official_draw(timeout=timeout_seconds, write_outputs=False) if live_bst_check else load_detection_report()
    if not detection:
        detection = {'status': 'not_checked', 'local_latest_draw': freshness.get('official_latest_draw', {}), 'official_latest_draw': {}}

    config = load_config()
    checkpoint = load_checkpoint()
    inspector = checkpoint_inspector()
    token = _read_json(TOKEN_JSON)
    history = list_activation_history(limit=20)
    backups = list_ingestion_backups()
    latest_event = history[0] if history else {}

    official_draw = detection.get('official_latest_draw') or {}
    local_draw = detection.get('local_latest_draw') or freshness.get('official_latest_draw') or {}
    detection_status = str(detection.get('status') or 'not_checked')
    bst_available = detection_status not in {'official_unavailable', 'captcha_blocked', 'check_failed', 'not_checked'} and bool(official_draw)
    diagnostics = detection.get('source_diagnostics') or {}
    connectivity = detection.get('connectivity') or {}
    failure_stage = detection.get('failure_stage')
    bst_operational_state = _bst_operational_state(
        live_bst_check=live_bst_check,
        detection_status=detection_status,
        bst_available=bst_available,
        failure_stage=failure_stage,
    )

    sources = freshness.get('sources') or []
    non_blocking_statuses = {'synced', 'informational', 'local_optional'}
    blocking_sources = [
        row for row in sources
        if row.get('key') != 'official' and str(row.get('status') or '') not in non_blocking_statuses
    ]
    synced_count = sum(1 for row in sources if row.get('status') == 'synced')
    out_of_sync_count = len(blocking_sources)
    unavailable_count = sum(1 for row in blocking_sources if row.get('status') in {'unavailable', 'missing'})
    ahead_count = sum(1 for row in blocking_sources if row.get('status') == 'ahead')
    behind_count = sum(1 for row in blocking_sources if row.get('status') == 'behind')

    token_exists = bool(token)
    token_consumed = bool(token.get('consumed')) if token_exists else False
    token_active = token_exists and not token_consumed
    recovery_ready = bool(backups) and all(bool(b.get('valid') and b.get('mirror_equal')) for b in backups)

    checks = {
        'bst_connectivity': bst_available,
        'local_draw_known': _draw_key(local_draw) != '—',
        'production_locked': bool(config.get('production_locked', True)),
        'operator_consent_valid': consent_is_valid(config),
        'token_active': token_active,
        'checkpoint_exists': bool(checkpoint),
        'primary_mirror_equal': bool(inspector.get('current_mirror_equal')),
        'downstream_fresh': out_of_sync_count == 0,
        'recovery_ready': recovery_ready,
    }

    if not checks['primary_mirror_equal']:
        health = 'critical'
    elif out_of_sync_count > 0 or detection_status in {'official_unavailable', 'captcha_blocked', 'check_failed'}:
        health = 'attention'
    else:
        health = 'healthy'

    report = {
        'step': '131',
        'name': 'Production Operations Dashboard & Health Summary',
        'generated_at_utc': utc_now(),
        'health': health,
        'live_bst_check': live_bst_check,
        'bst': {
            'available': bst_available,
            'status': detection_status,
            'official_draw_key': _draw_key(official_draw),
            'local_draw_key': _draw_key(local_draw),
            'draw_delta': detection.get('draw_delta'),
            'message': detection.get('message') or '',
            'failure_stage': failure_stage,
            'error_type': detection.get('error_type'),
            'connectivity': connectivity,
            'source_diagnostics': diagnostics,
            'operational_state': bst_operational_state,
        },
        'guardrails': {
            'production_locked': checks['production_locked'],
            'operator_consent_valid': checks['operator_consent_valid'],
            'token_exists': token_exists,
            'token_active': token_active,
            'token_target_draw_key': token.get('target_draw_key'),
            'checkpoint_exists': checks['checkpoint_exists'],
            'checkpoint_draw_key': checkpoint.get('draw_key') or checkpoint.get('target_draw_key'),
        },
        'freshness': {
            'overall_status': freshness.get('overall_status'),
            'synced_count': synced_count,
            'out_of_sync_count': out_of_sync_count,
            'unavailable_count': unavailable_count,
            'ahead_count': ahead_count,
            'behind_count': behind_count,
            'blocking_sources': blocking_sources,
            'sources': sources,
        },
        'activation': {
            'event_count': len(history),
            'latest_event': latest_event,
        },
        'recovery': {
            'backup_count': len(backups),
            'ready': recovery_ready,
            'primary_mirror_equal': checks['primary_mirror_equal'],
            'backups': backups[:10],
        },
        'checks': checks,
        'heavy_ml_retraining_performed': False,
    }
    if write_outputs:
        STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        STATUS_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        SUMMARY_MD.write_text(
            '# Step 131 — Production Operations Dashboard & Health Summary\n\n'
            f"- Health: **{health}**\n- Local draw: **{report['bst']['local_draw_key']}**\n"
            f"- Official draw: **{report['bst']['official_draw_key']}**\n- Out-of-sync modules: **{out_of_sync_count}**\n"
            f"- Production locked: **{checks['production_locked']}**\n- Recovery ready: **{recovery_ready}**\n",
            encoding='utf-8',
        )
    return report
