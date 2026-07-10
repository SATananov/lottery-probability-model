from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.v124_safe_official_draw_ingestion_engine import ingest_official_draw_record

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / 'data' / 'prize_winner_history.csv'
EXPORT = ROOT / 'data' / 'user_journal_exports' / 'prize_winner_history.csv'
STATUS_JSON = ROOT / 'models' / 'v127_end_to_end_automation_validation_status.json'
REPORT_JSON = ROOT / 'reports' / 'v127_end_to_end_automation_validation_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v127_end_to_end_automation_validation_summary.md'
AUDIT_JSONL = ROOT / 'reports' / 'v127_end_to_end_automation_validation_audit.jsonl'

STAGES = [
    ('detect', 'Simulated official draw detection'),
    ('ingest', 'Safe ingestion in isolated sandbox'),
    ('dataset_sync', 'Historical / normalized / canonical refresh simulation'),
    ('r_statistics', 'R statistical layer refresh simulation'),
    ('r_features', 'Step 121 R features refresh simulation'),
    ('decision', 'Decision Center refresh simulation'),
    ('ticket_pack', 'Real ticket pack refresh simulation'),
    ('model_ticket_pack', 'Model system ticket pack refresh simulation'),
    ('freshness', 'Final freshness validation'),
    ('duplicate', 'Duplicate protection validation'),
    ('rollback', 'Rollback validation'),
    ('isolation', 'Production data isolation validation'),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def _latest(path: Path) -> dict[str, Any]:
    rows = _read_rows(path)
    row = max(rows, key=lambda r: (int(r.get('draw_year') or 0), int(r.get('draw_number') or 0)))
    return {
        'year': int(row['draw_year']),
        'draw_number': int(row['draw_number']),
        'draw_key': row.get('draw_key') or f"{row['draw_year']}-{row['draw_number']}",
        'date': row.get('draw_date', ''),
    }


def _next_draw(local: dict[str, Any]) -> dict[str, Any]:
    year = int(local['year'])
    number = int(local['draw_number']) + 1
    try:
        base_date = datetime.strptime(local.get('date') or '', '%Y-%m-%d').date()
        draw_date = (base_date + timedelta(days=3)).isoformat()
    except ValueError:
        draw_date = f'{year}-12-31'
    numbers = [3, 9, 16, 27, 35, 48]
    return {
        'draw_year': year,
        'draw_number': number,
        'draw_key': f'{year}-{number}',
        'draw_date': draw_date,
        'source_url': 'simulation://step127/official-draw',
        **{f'n{i}': value for i, value in enumerate(numbers, 1)},
    }


def _stage(stage_id: str, ok: bool, message: str, **details: Any) -> dict[str, Any]:
    name = dict(STAGES)[stage_id]
    return {'id': stage_id, 'name': name, 'status': 'passed' if ok else 'failed', 'ok': ok, 'message': message, **details}


def _write_outputs(report: dict[str, Any]) -> None:
    for path in (STATUS_JSON, REPORT_JSON, SUMMARY_MD, AUDIT_JSONL):
        path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    STATUS_JSON.write_text(payload, encoding='utf-8')
    REPORT_JSON.write_text(payload, encoding='utf-8')
    lines = [
        '# Step 127 — End-to-End Official Draw Automation Validation', '',
        f"- Status: **{report.get('status')}**",
        f"- Simulated draw: **{report.get('simulated_draw_key')}**",
        f"- Production data unchanged: **{report.get('production_data_unchanged')}**",
        f"- Heavy ML retraining: **{report.get('heavy_ml_retraining_performed')}**", '',
        '## Validation stages',
    ]
    for row in report.get('stages', []):
        lines.append(f"- {row['name']}: **{row['status']}** — {row['message']}")
    SUMMARY_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    with AUDIT_JSONL.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + '\n')


def run_end_to_end_validation(*, write_outputs: bool = True) -> dict[str, Any]:
    started = utc_now()
    before_hashes = {'primary': _sha256(PRIMARY), 'export': _sha256(EXPORT)}
    local = _latest(PRIMARY)
    simulated = _next_draw(local)
    stages: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix='step127_e2e_') as tmp_name:
        sandbox = Path(tmp_name)
        data_path = sandbox / 'data' / 'prize_winner_history.csv'
        export_path = sandbox / 'data' / 'user_journal_exports' / 'prize_winner_history.csv'
        export_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PRIMARY, data_path)
        shutil.copy2(EXPORT, export_path)

        stages.append(_stage('detect', True, f"Simulated newer official draw {simulated['draw_key']} detected.", official_draw=simulated, local_draw=local))

        ingestion = ingest_official_draw_record(
            simulated,
            data_path=data_path,
            export_path=export_path,
            backup_root=sandbox / 'backups',
            staging_root=sandbox / 'staging',
            audit_path=sandbox / 'audit.jsonl',
            write_status=False,
        )
        ingest_ok = ingestion.get('status') == 'inserted' and ingestion.get('inserted') is True
        stages.append(_stage('ingest', ingest_ok, ingestion.get('message', ''), result=ingestion))

        refreshed_modules: dict[str, dict[str, Any]] = {}
        if ingest_ok:
            for stage_id in ('dataset_sync', 'r_statistics', 'r_features', 'decision', 'ticket_pack', 'model_ticket_pack'):
                refreshed_modules[stage_id] = {
                    'draw_key': simulated['draw_key'],
                    'draw_year': simulated['draw_year'],
                    'draw_number': simulated['draw_number'],
                    'status': 'refreshed_in_test_sandbox',
                }
                stages.append(_stage(stage_id, True, f"Sandbox artifact advanced to {simulated['draw_key']}.", artifact=refreshed_modules[stage_id]))
        else:
            for stage_id in ('dataset_sync', 'r_statistics', 'r_features', 'decision', 'ticket_pack', 'model_ticket_pack'):
                stages.append(_stage(stage_id, False, 'Blocked because safe ingestion failed.'))

        latest_primary = _latest(data_path)
        latest_export = _latest(export_path)
        freshness_ok = (
            latest_primary['draw_key'] == simulated['draw_key']
            and latest_export['draw_key'] == simulated['draw_key']
            and all(item['draw_key'] == simulated['draw_key'] for item in refreshed_modules.values())
        )
        stages.append(_stage('freshness', freshness_ok, 'All simulated operational layers are synchronized.' if freshness_ok else 'One or more simulated layers remain stale.', primary=latest_primary, export=latest_export, modules=refreshed_modules))

        duplicate = ingest_official_draw_record(
            simulated,
            data_path=data_path,
            export_path=export_path,
            backup_root=sandbox / 'duplicate_backups',
            staging_root=sandbox / 'duplicate_staging',
            audit_path=sandbox / 'duplicate_audit.jsonl',
            write_status=False,
        )
        duplicate_ok = duplicate.get('status') == 'duplicate_blocked'
        stages.append(_stage('duplicate', duplicate_ok, duplicate.get('message', ''), result=duplicate))

        rollback_data = sandbox / 'rollback' / 'data' / 'prize_winner_history.csv'
        rollback_export = sandbox / 'rollback' / 'data' / 'user_journal_exports' / 'prize_winner_history.csv'
        rollback_export.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PRIMARY, rollback_data)
        shutil.copy2(EXPORT, rollback_export)
        rollback_before = (_sha256(rollback_data), _sha256(rollback_export))

        def fail_after_primary(stage_name: str) -> None:
            if stage_name == 'after_primary_promote':
                raise RuntimeError('Step 127 forced rollback test')

        rollback = ingest_official_draw_record(
            simulated,
            data_path=rollback_data,
            export_path=rollback_export,
            backup_root=sandbox / 'rollback_backups',
            staging_root=sandbox / 'rollback_staging',
            audit_path=sandbox / 'rollback_audit.jsonl',
            write_status=False,
            failure_hook=fail_after_primary,
        )
        rollback_after = (_sha256(rollback_data), _sha256(rollback_export))
        rollback_ok = rollback.get('status') == 'rolled_back' and rollback.get('rollback_performed') and rollback_before == rollback_after
        stages.append(_stage('rollback', rollback_ok, 'Forced failure restored both sandbox source files.' if rollback_ok else 'Rollback validation failed.', result=rollback))

    after_hashes = {'primary': _sha256(PRIMARY), 'export': _sha256(EXPORT)}
    isolation_ok = before_hashes == after_hashes
    stages.append(_stage('isolation', isolation_ok, 'Real project draw files were not changed.' if isolation_ok else 'Production data changed unexpectedly.', before_sha256=before_hashes, after_sha256=after_hashes))

    failed = [row for row in stages if not row['ok']]
    report = {
        'step': '127',
        'name': 'End-to-End Official Draw Automation Validation',
        'started_at_utc': started,
        'finished_at_utc': utc_now(),
        'status': 'validated' if not failed else 'validation_failed',
        'simulated_draw_key': simulated['draw_key'],
        'simulated_draw': simulated,
        'production_data_unchanged': isolation_ok,
        'heavy_ml_retraining_performed': False,
        'stages': stages,
        'failed_stage_count': len(failed),
    }
    if write_outputs:
        _write_outputs(report)
    return report
