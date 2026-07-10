from __future__ import annotations

import hashlib
import io
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v131_production_operations_dashboard_engine import build_operations_snapshot

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / 'reports' / 'v132_production_incident_evidence_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v132_production_incident_evidence_summary.md'
EXPORT_DIR = ROOT / 'reports' / 'v132_incident_evidence_exports'

EVIDENCE_PATHS = (
    ROOT / 'data' / 'historical_draws.csv',
    ROOT / 'models' / 'v122_unified_official_draw_freshness_status.json',
    ROOT / 'models' / 'v123_bst_official_draw_detection_status.json',
    ROOT / 'models' / 'v126_startup_automation_status.json',
    ROOT / 'models' / 'v131_production_operations_dashboard_status.json',
    ROOT / 'reports' / 'v126_startup_automation_audit.jsonl',
    ROOT / 'reports' / 'v130_production_activation_audit.jsonl',
)

SENSITIVE_KEYS = {
    'token', 'token_value', 'activation_token', 'secret', 'password', 'api_key',
    'authorization', 'cookie', 'session',
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fingerprint(path: Path) -> dict[str, Any]:
    relative = path.relative_to(ROOT).as_posix()
    if not path.exists() or not path.is_file():
        return {'path': relative, 'exists': False, 'size_bytes': 0, 'sha256': None}
    data = path.read_bytes()
    return {
        'path': relative,
        'exists': True,
        'size_bytes': len(data),
        'sha256': _sha256_bytes(data),
    }


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in SENSITIVE_KEYS or normalized.endswith('_secret'):
                clean[key] = '[REDACTED]'
            else:
                clean[key] = _redact(item)
        return clean
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _operator_summary(evidence: dict[str, Any]) -> str:
    snapshot = evidence['operations_snapshot']
    bst = snapshot['bst']
    state = bst.get('operational_state') or {}
    return (
        '# Step 132 — Production Incident Evidence Bundle\n\n'
        f"- Bundle ID: **{evidence['bundle_id']}**\n"
        f"- Generated UTC: **{evidence['generated_at_utc']}**\n"
        f"- Production health: **{snapshot['health']}**\n"
        f"- BST operational state: **{state.get('code') or bst.get('status')}**\n"
        f"- Local draw: **{bst.get('local_draw_key')}**\n"
        f"- Official draw: **{bst.get('official_draw_key')}**\n"
        f"- Failure stage: **{bst.get('failure_stage') or 'none'}**\n"
        f"- Out-of-sync modules: **{snapshot['freshness']['out_of_sync_count']}**\n"
        f"- Production locked: **{snapshot['guardrails']['production_locked']}**\n"
        f"- Primary equals mirror: **{snapshot['recovery']['primary_mirror_equal']}**\n\n"
        'This evidence bundle is read-only and contains no activation token value or application secrets.\n'
    )


def build_incident_evidence(
    *,
    live_bst_check: bool = False,
    timeout_seconds: int = 15,
    write_outputs: bool = False,
) -> dict[str, Any]:
    snapshot = build_operations_snapshot(
        live_bst_check=live_bst_check,
        timeout_seconds=timeout_seconds,
        write_outputs=False,
    )
    sanitized_snapshot = _redact(snapshot)
    fingerprints = [_fingerprint(path) for path in EVIDENCE_PATHS]
    generated_at = utc_now()
    identity_basis = json.dumps(
        {
            'snapshot': sanitized_snapshot,
            'fingerprints': fingerprints,
            'python': platform.python_version(),
            'platform': platform.platform(),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    bundle_id = f"INC-{_sha256_bytes(identity_basis)[:16].upper()}"
    evidence = {
        'step': '132',
        'name': 'Production Incident Evidence Bundle & Safe Export',
        'bundle_id': bundle_id,
        'generated_at_utc': generated_at,
        'read_only': True,
        'secrets_redacted': True,
        'live_bst_check': live_bst_check,
        'runtime': {
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'platform': platform.platform(),
            'executable_name': Path(sys.executable).name,
        },
        'operations_snapshot': sanitized_snapshot,
        'file_fingerprints': fingerprints,
        'heavy_ml_retraining_performed': False,
        'production_state_changed': False,
    }
    evidence['operator_summary_md'] = _operator_summary(evidence)

    if write_outputs:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
        SUMMARY_MD.write_text(evidence['operator_summary_md'], encoding='utf-8')
    return evidence


def build_incident_evidence_zip(evidence: dict[str, Any]) -> bytes:
    safe_evidence = _redact(evidence)
    json_bytes = json.dumps(safe_evidence, ensure_ascii=False, indent=2).encode('utf-8')
    summary_bytes = str(safe_evidence.get('operator_summary_md') or '').encode('utf-8')
    checks_bytes = json.dumps(
        safe_evidence.get('operations_snapshot', {}).get('checks', {}),
        ensure_ascii=False,
        indent=2,
    ).encode('utf-8')
    manifest = {
        'bundle_id': safe_evidence.get('bundle_id'),
        'created_at_utc': safe_evidence.get('generated_at_utc'),
        'files': {
            'incident_evidence.json': _sha256_bytes(json_bytes),
            'operator_summary.md': _sha256_bytes(summary_bytes),
            'operational_checks.json': _sha256_bytes(checks_bytes),
        },
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('incident_evidence.json', json_bytes)
        archive.writestr('operator_summary.md', summary_bytes)
        archive.writestr('operational_checks.json', checks_bytes)
        archive.writestr('manifest.json', manifest_bytes)
    return buffer.getvalue()


def write_incident_evidence_export(evidence: dict[str, Any]) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_id = str(evidence.get('bundle_id') or 'INC-UNKNOWN')
    path = EXPORT_DIR / f'{bundle_id}.zip'
    path.write_bytes(build_incident_evidence_zip(evidence))
    return path
