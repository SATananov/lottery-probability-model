from __future__ import annotations

import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v132_production_incident_evidence_engine import build_incident_evidence, build_incident_evidence_zip
from src.v133_incident_evidence_integrity_engine import inspect_incident_evidence_zip
from src.v134_incident_evidence_registry_engine import (
    load_registry_events,
    rebuild_registry_status,
    register_bundle_created,
    register_verification_result,
    registry_events_csv,
)


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
    with tempfile.TemporaryDirectory() as directory:
        registry = Path(directory) / 'registry.jsonl'
        evidence = build_incident_evidence(live_bst_check=False, write_outputs=False)
        archive = build_incident_evidence_zip(evidence)
        created = register_bundle_created(evidence, archive, path=registry)
        assert created['event_type'] == 'CREATED'
        assert created['bundle_id'] == evidence['bundle_id']

        verified_result = inspect_incident_evidence_zip(archive, source_name='valid.zip')
        verified = register_verification_result(verified_result, path=registry)
        assert verified['event_type'] == 'VERIFIED'

        invalid_result = inspect_incident_evidence_zip(tamper_archive(archive), source_name='tampered.zip')
        invalid = register_verification_result(invalid_result, path=registry)
        assert invalid['event_type'] == 'INVALID'
        assert invalid['failed_check_count'] > 0

        events = load_registry_events(registry)
        assert len(events) == 3, json.dumps(events, ensure_ascii=False, indent=2)
        status = rebuild_registry_status(write_outputs=False, path=registry)
        assert status['bundle_count'] == 1
        assert status['created_count'] == 1
        assert status['verified_count'] == 1
        assert status['invalid_count'] == 1
        assert status['production_state_changed'] is False
        csv_bytes = registry_events_csv(events)
        assert b'archive_sha256' in csv_bytes
        assert evidence['bundle_id'].encode() in csv_bytes

    print('STEP_134_VERIFY_OK')


if __name__ == '__main__':
    main()
