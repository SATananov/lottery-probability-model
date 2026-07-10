from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v127_end_to_end_automation_validation_engine import PRIMARY, EXPORT, run_end_to_end_validation


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    before = (sha(PRIMARY), sha(EXPORT))
    report = run_end_to_end_validation(write_outputs=False)
    after = (sha(PRIMARY), sha(EXPORT))
    assert report['status'] == 'validated', report
    assert report['failed_stage_count'] == 0, report
    assert report['production_data_unchanged'] is True, report
    assert report['heavy_ml_retraining_performed'] is False, report
    assert before == after, (before, after)
    stage_ids = {row['id'] for row in report['stages'] if row['ok']}
    required = {'detect','ingest','dataset_sync','r_statistics','r_features','decision','ticket_pack','model_ticket_pack','freshness','duplicate','rollback','isolation'}
    assert required <= stage_ids, stage_ids
    print('STEP_127_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
