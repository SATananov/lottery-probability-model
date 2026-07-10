from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v132_production_incident_evidence_engine import build_incident_evidence, build_incident_evidence_zip
from src.v133_incident_evidence_integrity_engine import inspect_incident_evidence_zip


def tamper_archive(original: bytes) -> bytes:
    source = zipfile.ZipFile(io.BytesIO(original), 'r')
    buffer = io.BytesIO()
    with source, zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            payload = source.read(info.filename)
            if info.filename == 'operator_summary.md':
                payload += b'\nTAMPERED\n'
            target.writestr(info.filename, payload)
    return buffer.getvalue()


def main() -> None:
    evidence = build_incident_evidence(live_bst_check=False, write_outputs=False)
    archive = build_incident_evidence_zip(evidence)
    valid = inspect_incident_evidence_zip(archive, source_name='valid.zip')
    assert valid['verdict'] == 'verified', json.dumps(valid, ensure_ascii=False, indent=2)
    assert valid['bundle_id'] == evidence['bundle_id']
    assert valid['failed_check_count'] == 0
    assert valid['production_state_changed'] is False

    tampered = inspect_incident_evidence_zip(tamper_archive(archive), source_name='tampered.zip')
    assert tampered['verdict'] == 'invalid'
    assert any(item['code'] == 'manifest_checksums_match' and not item['passed'] for item in tampered['checks'])

    invalid = inspect_incident_evidence_zip(b'not-a-zip', source_name='invalid.zip')
    assert invalid['verdict'] == 'invalid'
    assert any(item['code'] == 'valid_zip' and not item['passed'] for item in invalid['checks'])

    print('STEP_133_VERIFY_OK')


if __name__ == '__main__':
    main()
