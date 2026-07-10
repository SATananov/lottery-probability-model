from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / 'reports' / 'v133_incident_evidence_integrity_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v133_incident_evidence_integrity_summary.md'

REQUIRED_FILES = {
    'incident_evidence.json',
    'operator_summary.md',
    'operational_checks.json',
    'manifest.json',
}
PROHIBITED_KEYS = {
    'token_value', 'activation_token', 'secret', 'password', 'api_key',
    'authorization', 'cookie', 'session',
}
MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_MEMBER_BYTES = 10 * 1024 * 1024
MAX_MEMBER_COUNT = 32


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_member_name(name: str) -> bool:
    path = Path(name)
    return not path.is_absolute() and '..' not in path.parts and '\\' not in name


def _find_prohibited_keys(value: Any, *, prefix: str = '') -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            location = f'{prefix}.{key}' if prefix else str(key)
            if normalized in PROHIBITED_KEYS or normalized.endswith('_secret'):
                if item not in (None, '', '[REDACTED]'):
                    found.append(location)
            found.extend(_find_prohibited_keys(item, prefix=location))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_find_prohibited_keys(item, prefix=f'{prefix}[{index}]'))
    return found


def inspect_incident_evidence_zip(
    archive_bytes: bytes,
    *,
    source_name: str = 'incident-evidence.zip',
    write_outputs: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(code: str, passed: bool, message: str) -> None:
        checks.append({'code': code, 'passed': bool(passed), 'message': message})

    archive_sha256 = _sha256(archive_bytes)
    result: dict[str, Any] = {
        'step': '133',
        'name': 'Incident Evidence Integrity & Chain-of-Custody Inspector',
        'checked_at_utc': utc_now(),
        'source_name': Path(source_name).name,
        'archive_size_bytes': len(archive_bytes),
        'archive_sha256': archive_sha256,
        'read_only': True,
        'production_state_changed': False,
        'checks': checks,
        'bundle_id': None,
        'manifest_created_at_utc': None,
        'member_count': 0,
        'member_fingerprints': [],
        'prohibited_key_paths': [],
    }

    record('archive_not_empty', bool(archive_bytes), 'Archive contains bytes.' if archive_bytes else 'Archive is empty.')
    record(
        'archive_size_limit',
        len(archive_bytes) <= MAX_ARCHIVE_BYTES,
        f'Archive size is {len(archive_bytes)} bytes; limit is {MAX_ARCHIVE_BYTES}.',
    )
    if not archive_bytes or len(archive_bytes) > MAX_ARCHIVE_BYTES:
        return _finalize(result, write_outputs=write_outputs)

    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes), mode='r')
    except (zipfile.BadZipFile, OSError) as exc:
        record('valid_zip', False, f'Invalid ZIP: {type(exc).__name__}: {exc}')
        return _finalize(result, write_outputs=write_outputs)

    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        result['member_count'] = len(infos)
        record('valid_zip', True, 'ZIP central directory is valid.')
        record('member_count_limit', len(infos) <= MAX_MEMBER_COUNT, f'{len(infos)} members; limit is {MAX_MEMBER_COUNT}.')
        record('safe_member_paths', all(_safe_member_name(name) for name in names), 'All member paths are safe.')
        record('no_duplicate_members', len(names) == len(set(names)), 'No duplicate member names detected.')
        record('required_files_present', REQUIRED_FILES.issubset(set(names)), 'Required evidence files are present.')
        oversized = [info.filename for info in infos if info.file_size > MAX_MEMBER_BYTES]
        record('member_size_limit', not oversized, 'No oversized members.' if not oversized else f'Oversized: {oversized}')

        if not all(check['passed'] for check in checks[-5:]):
            return _finalize(result, write_outputs=write_outputs)

        member_bytes: dict[str, bytes] = {}
        try:
            for info in infos:
                payload = archive.read(info.filename)
                member_bytes[info.filename] = payload
                result['member_fingerprints'].append({
                    'path': info.filename,
                    'size_bytes': len(payload),
                    'sha256': _sha256(payload),
                })
        except (RuntimeError, zipfile.BadZipFile, OSError) as exc:
            record('members_readable', False, f'Unable to read members: {type(exc).__name__}: {exc}')
            return _finalize(result, write_outputs=write_outputs)
        record('members_readable', True, 'All members are readable.')

        try:
            manifest = json.loads(member_bytes['manifest.json'].decode('utf-8'))
            evidence = json.loads(member_bytes['incident_evidence.json'].decode('utf-8'))
            checks_payload = json.loads(member_bytes['operational_checks.json'].decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            record('json_documents_valid', False, f'JSON validation failed: {type(exc).__name__}: {exc}')
            return _finalize(result, write_outputs=write_outputs)
        record('json_documents_valid', True, 'Manifest, evidence and operational checks are valid JSON.')

        result['bundle_id'] = manifest.get('bundle_id')
        result['manifest_created_at_utc'] = manifest.get('created_at_utc')
        declared = manifest.get('files') if isinstance(manifest.get('files'), dict) else {}
        checksum_results: list[dict[str, Any]] = []
        for name, expected in declared.items():
            actual = _sha256(member_bytes[name]) if name in member_bytes else None
            checksum_results.append({
                'path': name,
                'expected_sha256': expected,
                'actual_sha256': actual,
                'matches': bool(actual and actual == expected),
            })
        result['manifest_checksum_results'] = checksum_results
        declared_expected = REQUIRED_FILES - {'manifest.json'}
        checksum_ok = declared_expected.issubset(set(declared)) and all(item['matches'] for item in checksum_results)
        record('manifest_checksums_match', checksum_ok, 'Manifest checksums match.' if checksum_ok else 'Manifest checksum mismatch or incomplete declaration.')

        evidence_bundle_id = evidence.get('bundle_id') if isinstance(evidence, dict) else None
        record(
            'bundle_identity_consistent',
            bool(result['bundle_id']) and result['bundle_id'] == evidence_bundle_id,
            'Bundle ID matches manifest and evidence document.',
        )
        record(
            'read_only_claims_present',
            evidence.get('read_only') is True and evidence.get('production_state_changed') is False,
            'Evidence records read-only execution and no production mutation.',
        )
        record(
            'checks_document_consistent',
            checks_payload == evidence.get('operations_snapshot', {}).get('checks', {}),
            'Operational checks document matches the evidence snapshot.',
        )
        prohibited = _find_prohibited_keys(evidence)
        result['prohibited_key_paths'] = prohibited
        record('no_exposed_secrets', not prohibited, 'No non-redacted prohibited fields detected.' if not prohibited else f'Potential exposed fields: {prohibited}')

    return _finalize(result, write_outputs=write_outputs)


def _summary(result: dict[str, Any]) -> str:
    failed = [item for item in result['checks'] if not item['passed']]
    verdict = result.get('verdict', 'invalid').upper()
    lines = [
        '# Step 133 — Incident Evidence Integrity Report',
        '',
        f"- Verdict: **{verdict}**",
        f"- Bundle ID: **{result.get('bundle_id') or 'unknown'}**",
        f"- Archive SHA-256: `{result.get('archive_sha256')}`",
        f"- Archive size: **{result.get('archive_size_bytes')} bytes**",
        f"- Checked UTC: **{result.get('checked_at_utc')}**",
        f"- Failed checks: **{len(failed)}**",
        '',
        '## Checks',
        '',
    ]
    for item in result['checks']:
        marker = 'PASS' if item['passed'] else 'FAIL'
        lines.append(f"- **{marker} · {item['code']}** — {item['message']}")
    lines.extend(['', 'Inspector is read-only and does not modify production state.', ''])
    return '\n'.join(lines)


def _finalize(result: dict[str, Any], *, write_outputs: bool) -> dict[str, Any]:
    result['failed_check_count'] = sum(1 for item in result['checks'] if not item['passed'])
    result['passed_check_count'] = sum(1 for item in result['checks'] if item['passed'])
    result['verdict'] = 'verified' if result['checks'] and result['failed_check_count'] == 0 else 'invalid'
    result['summary_md'] = _summary(result)
    if write_outputs:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        SUMMARY_MD.write_text(result['summary_md'], encoding='utf-8')
    return result
