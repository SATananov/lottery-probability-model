from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v135_incident_evidence_retention_engine import (
    ARCHIVE_CONFIRMATION,
    CLEANUP_CONFIRMATION,
    apply_archive_plan,
    apply_cleanup_plan,
    build_retention_plan,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_event(path: Path, payload: dict) -> None:
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(payload) + '\n')


def main() -> None:
    now = datetime(2026, 7, 10, tzinfo=timezone.utc)
    policy = {
        'retention_days_active': 30,
        'archive_cleanup_days': 180,
        'minimum_active_verified_bundles': 1,
        'protect_invalid_bundles': True,
        'protect_unverified_bundles': True,
        'registry_is_append_only': True,
        'dry_run_default': True,
    }
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        exports = root / 'exports'
        archive = root / 'archive'
        registry = root / 'registry.jsonl'
        audit = root / 'audit.jsonl'
        exports.mkdir()
        archive.mkdir()

        bundles = [
            ('INC-NEW', now - timedelta(days=2), 'verified'),
            ('INC-OLD', now - timedelta(days=60), 'verified'),
            ('INC-BAD', now - timedelta(days=90), 'invalid'),
            ('INC-UNCHECKED', now - timedelta(days=90), None),
        ]
        for bundle_id, created, verdict in bundles:
            payload = f'{bundle_id}-evidence'.encode()
            path = exports / f'{bundle_id}.zip'
            path.write_bytes(payload)
            stamp = created.timestamp()
            os.utime(path, (stamp, stamp))
            write_event(registry, {
                'event_type': 'CREATED', 'bundle_id': bundle_id,
                'recorded_at_utc': created.isoformat(), 'archive_sha256': sha256(path),
                'source_name': path.name,
            })
            if verdict:
                write_event(registry, {
                    'event_type': 'VERIFIED' if verdict == 'verified' else 'INVALID',
                    'bundle_id': bundle_id, 'recorded_at_utc': (created + timedelta(hours=1)).isoformat(),
                    'archive_sha256': sha256(path), 'source_name': path.name, 'verdict': verdict,
                })

        expired = archive / 'INC-EXPIRED.zip'
        expired.write_bytes(b'expired')
        expired_stamp = (now - timedelta(days=200)).timestamp()
        os.utime(expired, (expired_stamp, expired_stamp))

        registry_before = registry.read_bytes()
        plan = build_retention_plan(now=now, policy=policy, export_dir=exports, archive_dir=archive, registry_path=registry)
        assert [item['bundle_id'] for item in plan['archive_candidates']] == ['INC-OLD']
        protected_ids = {item['bundle_id'] for item in plan['protected']}
        assert {'INC-NEW', 'INC-BAD', 'INC-UNCHECKED'} <= protected_ids
        assert len(plan['cleanup_candidates']) == 1
        assert plan['production_state_changed'] is False
        assert registry.read_bytes() == registry_before

        try:
            apply_archive_plan(plan, confirmation='wrong', archive_dir=archive, audit_path=audit)
            raise AssertionError('Wrong archive confirmation was accepted.')
        except PermissionError:
            pass
        archived = apply_archive_plan(plan, confirmation=ARCHIVE_CONFIRMATION, archive_dir=archive, audit_path=audit)
        assert archived['item_count'] == 1
        assert not (exports / 'INC-OLD.zip').exists()
        assert (archive / 'INC-OLD.zip').exists()
        assert registry.read_bytes() == registry_before

        cleanup_plan = build_retention_plan(now=now, policy=policy, export_dir=exports, archive_dir=archive, registry_path=registry)
        cleaned = apply_cleanup_plan(cleanup_plan, confirmation=CLEANUP_CONFIRMATION, audit_path=audit)
        assert cleaned['item_count'] == 1
        assert not expired.exists()
        assert (archive / 'INC-OLD.zip').exists()
        assert registry.read_bytes() == registry_before
        assert audit.exists() and len(audit.read_text(encoding='utf-8').splitlines()) == 2

    print('STEP_135_VERIFY_OK')


if __name__ == '__main__':
    main()
