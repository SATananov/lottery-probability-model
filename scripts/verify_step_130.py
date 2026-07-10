from __future__ import annotations

import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v130_production_activation_audit_recovery_engine import (
    RECOVERY_PHRASE,
    build_recovery_preflight,
    execute_recovery,
    list_activation_history,
    list_ingestion_backups,
)


def _write_csv(path: Path, latest_number: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'draw_year,draw_number,draw_key,draw_date,n1,n2,n3,n4,n5,n6\n'
        f'2026,{latest_number},2026-{latest_number},2026-07-09,1,2,3,4,5,6\n',
        encoding='utf-8',
    )


def main() -> int:
    required = [
        ROOT / 'src' / 'v130_production_activation_audit_recovery_engine.py',
        ROOT / 'src' / 'v130_production_activation_audit_recovery_section.py',
        ROOT / 'tools' / 'run_production_audit_recovery_console.py',
    ]
    assert all(p.exists() for p in required)
    with tempfile.TemporaryDirectory(prefix='step130_verify_') as tmp:
        base = Path(tmp)
        data = base / 'data' / 'prize_winner_history.csv'
        mirror = base / 'data' / 'user_journal_exports' / 'prize_winner_history.csv'
        backup_root = base / 'backups'
        backup = backup_root / 'backup-001'
        _write_csv(data, 54)
        _write_csv(mirror, 54)
        _write_csv(backup / 'prize_winner_history.csv', 53)
        _write_csv(backup / 'user_journal_exports' / 'prize_winner_history.csv', 53)

        backups = list_ingestion_backups(backup_root)
        assert backups and backups[0]['valid'] and backups[0]['latest_draw_key'] == '2026-53'
        preflight = build_recovery_preflight('backup-001', backup_root=backup_root, data_path=data, export_path=mirror)
        assert preflight['ready']
        dry = execute_recovery('backup-001', 'Verifier', '', dry_run=True, backup_root=backup_root, data_path=data, export_path=mirror, audit_path=base / 'audit.jsonl', write_outputs=False)
        assert dry['status'] == 'dry_run_ready' and not dry['production_data_changed']
        blocked = execute_recovery('backup-001', 'Verifier', 'wrong', dry_run=False, backup_root=backup_root, data_path=data, export_path=mirror, audit_path=base / 'audit.jsonl', write_outputs=False)
        assert blocked['status'] == 'blocked'
        recovered = execute_recovery('backup-001', 'Verifier', RECOVERY_PHRASE, dry_run=False, backup_root=backup_root, data_path=data, export_path=mirror, audit_path=base / 'audit.jsonl', write_outputs=False)
        assert recovered['status'] == 'recovered' and recovered['production_data_changed']
        assert '2026-53' in data.read_text(encoding='utf-8')
        assert list_activation_history(limit=5) is not None
    print('STEP_130_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
