from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.bst_official_sync_engine import DATA_PATH, EXPORT_PATH, read_rows
from src.v124_safe_official_draw_ingestion_engine import BACKUP_ROOT
from src.v128_production_auto_apply_guardrails_engine import CHECKPOINT_JSON, load_checkpoint

ROOT = Path(__file__).resolve().parents[1]
V128_AUDIT = ROOT / 'reports' / 'v128_production_guardrails_audit.jsonl'
V129_AUDIT = ROOT / 'reports' / 'v129_controlled_production_activation_audit.jsonl'
RECOVERY_AUDIT = ROOT / 'reports' / 'v130_production_activation_recovery_audit.jsonl'
STATUS_JSON = ROOT / 'models' / 'v130_production_activation_audit_recovery_status.json'
REPORT_JSON = ROOT / 'reports' / 'v130_production_activation_audit_recovery_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v130_production_activation_audit_recovery_summary.md'
RECOVERY_PHRASE = 'ВЪЗСТАНОВИ ПОСЛЕДНИЯ BACKUP'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _read_jsonl(path: Path, source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            rows.append({'source': source, 'line_no': line_no, 'status': 'invalid_json'})
            continue
        if isinstance(item, dict):
            item = dict(item)
            item['source'] = source
            item['line_no'] = line_no
            rows.append(item)
    return rows


def _event_time(item: dict[str, Any]) -> str:
    return str(item.get('finished_at_utc') or item.get('started_at_utc') or item.get('created_at_utc') or '')


def _operator_identity(item: dict[str, Any]) -> str:
    explicit = item.get('operator') or item.get('operator_id') or item.get('operator_name')
    if explicit:
        return str(explicit)
    trigger = str(item.get('trigger') or (item.get('guarded_report') or {}).get('trigger') or '')
    if trigger:
        return trigger
    return 'local_operator'


def list_activation_history(limit: int = 100) -> list[dict[str, Any]]:
    events = _read_jsonl(V128_AUDIT, 'step128_guardrails') + _read_jsonl(V129_AUDIT, 'step129_activation') + _read_jsonl(RECOVERY_AUDIT, 'step130_recovery')
    normalized: list[dict[str, Any]] = []
    for item in events:
        target = item.get('target_draw_key')
        if not target:
            target = ((item.get('preflight') or {}).get('target_draw_key') or
                      (((item.get('automation_report') or {}).get('detection') or {}).get('official_latest_draw') or {}).get('draw_key'))
        normalized.append({
            'timestamp_utc': _event_time(item),
            'source': item.get('source'),
            'mode': item.get('mode') or item.get('trigger') or item.get('name') or '',
            'status': item.get('status') or '',
            'operator': _operator_identity(item),
            'target_draw_key': target or '',
            'activation_executed': bool(item.get('activation_executed', False)),
            'token_consumed': bool(item.get('token_consumed', False)),
            'production_data_changed': bool(item.get('production_data_changed', False)),
            'message': item.get('message') or '',
            'raw': item,
        })
    normalized.sort(key=lambda row: row['timestamp_utc'], reverse=True)
    return normalized[:max(1, min(1000, int(limit)))]


def list_ingestion_backups(backup_root: Path = BACKUP_ROOT) -> list[dict[str, Any]]:
    backups: list[dict[str, Any]] = []
    if not backup_root.exists():
        return backups
    for folder in sorted((p for p in backup_root.iterdir() if p.is_dir()), reverse=True):
        primary = folder / 'prize_winner_history.csv'
        mirror = folder / 'user_journal_exports' / 'prize_winner_history.csv'
        valid = primary.exists() and mirror.exists()
        mirror_equal = valid and _sha256(primary) == _sha256(mirror)
        latest_key = ''
        row_count = 0
        if valid:
            try:
                rows = read_rows(primary)
                row_count = len(rows)
                if rows:
                    latest = max(rows, key=lambda r: (int(r.get('draw_year') or 0), int(r.get('draw_number') or 0)))
                    latest_key = str(latest.get('draw_key') or f"{latest.get('draw_year')}-{latest.get('draw_number')}")
            except Exception:
                valid = False
        backups.append({
            'backup_id': folder.name,
            'backup_dir': str(folder),
            'primary_path': str(primary),
            'mirror_path': str(mirror),
            'valid': valid,
            'mirror_equal': mirror_equal,
            'row_count': row_count,
            'latest_draw_key': latest_key,
            'sha256': _sha256(primary) if primary.exists() else '',
        })
    return backups


def checkpoint_inspector() -> dict[str, Any]:
    checkpoint = load_checkpoint()
    token = _read_json(ROOT / 'models' / 'v129_one_time_activation_token.json')
    return {
        'checkpoint_path': str(CHECKPOINT_JSON),
        'checkpoint_exists': CHECKPOINT_JSON.exists(),
        'checkpoint': checkpoint,
        'token_state': {
            'exists': bool(token),
            'target_draw_key': token.get('target_draw_key'),
            'issued_at_utc': token.get('issued_at_utc'),
            'expires_at_utc': token.get('expires_at_utc'),
            'consumed': token.get('consumed'),
            'consumed_at_utc': token.get('consumed_at_utc'),
        },
        'current_primary_sha256': _sha256(DATA_PATH) if DATA_PATH.exists() else '',
        'current_mirror_sha256': _sha256(EXPORT_PATH) if EXPORT_PATH.exists() else '',
        'current_mirror_equal': DATA_PATH.exists() and EXPORT_PATH.exists() and _sha256(DATA_PATH) == _sha256(EXPORT_PATH),
    }


def build_recovery_preflight(backup_id: str, *, backup_root: Path = BACKUP_ROOT, data_path: Path = DATA_PATH, export_path: Path = EXPORT_PATH) -> dict[str, Any]:
    selected = next((b for b in list_ingestion_backups(backup_root) if b['backup_id'] == backup_id), None)
    checks = {
        'backup_selected': selected is not None,
        'backup_valid': bool(selected and selected['valid']),
        'backup_mirror_equal': bool(selected and selected['mirror_equal']),
        'current_primary_exists': data_path.exists(),
        'current_mirror_exists': export_path.exists(),
    }
    return {
        'step': '130',
        'created_at_utc': utc_now(),
        'backup': selected or {},
        'checks': checks,
        'ready': all(checks.values()),
        'data_path': str(data_path),
        'export_path': str(export_path),
        'production_data_changed': False,
    }


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix='step130_recovery_', suffix=destination.suffix, dir=destination.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        shutil.copy2(source, tmp)
        os.replace(tmp, destination)
    finally:
        tmp.unlink(missing_ok=True)


def execute_recovery(
    backup_id: str,
    operator: str,
    confirmation_phrase: str,
    *,
    dry_run: bool = True,
    backup_root: Path = BACKUP_ROOT,
    data_path: Path = DATA_PATH,
    export_path: Path = EXPORT_PATH,
    audit_path: Path = RECOVERY_AUDIT,
    write_outputs: bool = True,
) -> dict[str, Any]:
    preflight = build_recovery_preflight(backup_id, backup_root=backup_root, data_path=data_path, export_path=export_path)
    report: dict[str, Any] = {
        'step': '130',
        'name': 'Production Activation Audit & Recovery Console',
        'started_at_utc': utc_now(),
        'finished_at_utc': utc_now(),
        'mode': 'recovery_dry_run' if dry_run else 'recovery_execute',
        'status': 'blocked',
        'operator': operator.strip() or 'unknown_operator',
        'backup_id': backup_id,
        'target_draw_key': (preflight.get('backup') or {}).get('latest_draw_key'),
        'preflight': preflight,
        'recovery_executed': False,
        'rollback_performed': False,
        'production_data_changed': False,
        'message': '',
        'heavy_ml_retraining_performed': False,
    }
    if not preflight['ready']:
        report['message'] = 'Recovery preflight е блокиран.'
    elif dry_run:
        report['status'] = 'dry_run_ready'
        report['message'] = 'Recovery dry-run е готов; production данните не са променени.'
    elif confirmation_phrase.strip() != RECOVERY_PHRASE:
        report['message'] = 'Фразата за recovery потвърждение не съвпада.'
    elif not operator.strip():
        report['message'] = 'Липсва операторска идентичност.'
    else:
        backup = preflight['backup']
        emergency_root = backup_root / '_step130_emergency_before_recovery' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
        emergency_primary = emergency_root / 'prize_winner_history.csv'
        emergency_mirror = emergency_root / 'user_journal_exports' / 'prize_winner_history.csv'
        emergency_mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(data_path, emergency_primary)
        shutil.copy2(export_path, emergency_mirror)
        try:
            _atomic_copy(Path(backup['primary_path']), data_path)
            _atomic_copy(Path(backup['mirror_path']), export_path)
            if _sha256(data_path) != _sha256(export_path):
                raise RuntimeError('Recovered primary and mirror are not identical.')
            report.update(
                status='recovered',
                message='Production source of truth е възстановен от избрания backup.',
                recovery_executed=True,
                rollback_performed=True,
                production_data_changed=True,
                emergency_backup_dir=str(emergency_root),
                restored_sha256=_sha256(data_path),
            )
        except Exception as exc:
            _atomic_copy(emergency_primary, data_path)
            _atomic_copy(emergency_mirror, export_path)
            report.update(status='recovery_failed_rolled_back', message='Recovery се провали и текущите production данни бяха възстановени.', error_type=type(exc).__name__, error=str(exc), rollback_performed=True)
    report['finished_at_utc'] = utc_now()
    if write_outputs:
        STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        STATUS_JSON.write_text(payload, encoding='utf-8')
        REPORT_JSON.write_text(payload, encoding='utf-8')
        SUMMARY_MD.write_text('\n'.join([
            '# Step 130 — Production Activation Audit & Recovery Console', '',
            f"- Status: **{report.get('status')}**",
            f"- Mode: **{report.get('mode')}**",
            f"- Operator: **{report.get('operator')}**",
            f"- Backup: **{report.get('backup_id')}**",
            f"- Recovery executed: **{report.get('recovery_executed')}**",
            f"- Production data changed: **{report.get('production_data_changed')}**", '',
            str(report.get('message') or ''), ''
        ]), encoding='utf-8')
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + '\n')
    return report


def build_console_snapshot() -> dict[str, Any]:
    snapshot = {
        'step': '130',
        'created_at_utc': utc_now(),
        'history': list_activation_history(),
        'checkpoint': checkpoint_inspector(),
        'backups': list_ingestion_backups(),
    }
    snapshot['history_count'] = len(snapshot['history'])
    snapshot['backup_count'] = len(snapshot['backups'])
    return snapshot
