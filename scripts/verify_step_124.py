from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from src.v124_safe_official_draw_ingestion_engine import ingest_official_draw_record


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def synthetic(draw_number: int) -> dict[str, str]:
    return {
        'draw_year': '2026', 'draw_number': str(draw_number), 'draw_date': '2026-07-12',
        'n1': '1', 'n2': '7', 'n3': '14', 'n4': '22', 'n5': '35', 'n6': '49',
        'jackpot_eur': '1000000.00', 'winners_6': '0', 'prize_6_eur': '0', 'total_6_eur': '0',
        'winners_5': '1', 'prize_5_eur': '1', 'total_5_eur': '1',
        'winners_4': '1', 'prize_4_eur': '1', 'total_4_eur': '1',
        'winners_3': '1', 'prize_3_eur': '1', 'total_3_eur': '1',
        'source_url': f'https://info.toto.bg/results/6x49/2026-{draw_number}',
        'note': 'Step 124 verifier synthetic official draw',
    }


def main() -> int:
    required = [
        ROOT / 'src/v124_safe_official_draw_ingestion_engine.py',
        ROOT / 'src/v124_safe_official_draw_ingestion_section.py',
        ROOT / 'tools/ingest_latest_bst_official_draw.py',
    ]
    for path in required:
        assert path.exists(), f'missing {path}'
    app = (ROOT / 'streamlit_app.py').read_text(encoding='utf-8')
    assert 'render_v124_safe_official_draw_ingestion_section' in app
    assert 'Безопасно прилагане на официален тираж' in app

    with tempfile.TemporaryDirectory(prefix='step124_verify_') as tmp:
        base = Path(tmp)
        data = base / 'data/prize_winner_history.csv'
        export = base / 'data/user_journal_exports/prize_winner_history.csv'
        data.parent.mkdir(parents=True)
        export.parent.mkdir(parents=True)
        source = ROOT / 'data/prize_winner_history.csv'
        data.write_bytes(source.read_bytes())
        export.write_bytes(source.read_bytes())
        before_count = len(read(data))
        next_draw = max(int(r['draw_number']) for r in read(data) if r.get('draw_year') == '2026') + 1

        common = dict(
            data_path=data, export_path=export,
            backup_root=base / 'backups', staging_root=base / 'staging',
            audit_path=base / 'audit.jsonl', write_status=False,
        )
        inserted = ingest_official_draw_record(synthetic(next_draw), **common)
        assert inserted['status'] == 'inserted', inserted
        assert inserted['inserted'] is True
        assert inserted['backup_created'] is True
        assert inserted['staging_validated'] is True
        assert inserted['downstream_refresh_started'] is False
        assert len(read(data)) == before_count + 1
        assert sha(data) == sha(export)

        duplicate_hash = sha(data)
        gap = ingest_official_draw_record(synthetic(next_draw + 2), **common)
        assert gap['status'] == 'draw_gap_blocked', gap
        assert sha(data) == duplicate_hash

        duplicate = ingest_official_draw_record(synthetic(next_draw), **common)
        assert duplicate['status'] == 'duplicate_blocked', duplicate
        assert duplicate['duplicate_blocked'] is True
        assert sha(data) == duplicate_hash

        rollback_before = sha(data)
        def fail(stage: str) -> None:
            if stage == 'after_primary_promote':
                raise RuntimeError('forced verifier failure')
        rolled = ingest_official_draw_record(synthetic(next_draw + 1), failure_hook=fail, **common)
        assert rolled['status'] == 'rolled_back', rolled
        assert rolled['rollback_performed'] is True
        assert sha(data) == rollback_before
        assert sha(data) == sha(export)
        audit_lines = (base / 'audit.jsonl').read_text(encoding='utf-8').strip().splitlines()
        assert len(audit_lines) == 4
        for line in audit_lines:
            json.loads(line)

    print('STEP_124_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
