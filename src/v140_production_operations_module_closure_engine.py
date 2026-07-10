from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v140_production_operations_module_closure_status.json'
SUMMARY_MD = ROOT / 'reports' / 'v140_production_operations_module_closure_summary.md'

MODULE_NAME = 'Production Operations / Incident Evidence / Recovery Governance'
STEP_RANGE = '131-140'

REQUIRED_COMPONENTS: dict[str, list[str]] = {
    'dashboard': [
        'src/v131_production_operations_dashboard_engine.py',
        'src/v131_production_operations_dashboard_section.py',
        'tools/run_production_operations_dashboard.py',
    ],
    'incident_evidence': [
        'src/v132_production_incident_evidence_engine.py',
        'src/v132_production_incident_evidence_section.py',
        'src/v133_incident_evidence_integrity_engine.py',
        'src/v133_incident_evidence_integrity_section.py',
        'src/v134_incident_evidence_registry_engine.py',
        'src/v134_incident_evidence_registry_section.py',
        'src/v135_incident_evidence_retention_engine.py',
        'src/v135_incident_evidence_retention_section.py',
    ],
    'recovery_governance': [
        'src/v136_incident_evidence_recovery_drill_engine.py',
        'src/v136_incident_evidence_recovery_drill_section.py',
        'src/v137_recovery_drill_audit_reconciliation_engine.py',
        'src/v137_recovery_drill_audit_reconciliation_section.py',
        'src/v138_recovery_exception_sla_engine.py',
        'src/v138_recovery_exception_sla_section.py',
        'src/v139_recovery_exception_management_summary_engine.py',
        'src/v139_recovery_exception_management_summary_section.py',
    ],
    'verification': [
        'scripts/verify_step_131.py',
        'scripts/verify_step_131_2.py',
        'scripts/verify_step_131_3.py',
        'scripts/verify_step_131_4.py',
        'scripts/verify_step_132.py',
        'scripts/verify_step_133.py',
        'scripts/verify_step_134.py',
        'scripts/verify_step_135.py',
        'scripts/verify_step_136.py',
        'scripts/verify_step_137.py',
        'scripts/verify_step_138.py',
        'scripts/verify_step_139.py',
        'scripts/verify_step_140.py',
    ],
}

READ_ONLY_BOUNDARIES = [
    'No official draw is automatically applied by the closure layer.',
    'No production lock or activation token is changed.',
    'No evidence archive, registry or append-only audit is rewritten.',
    'No automatic production restore is performed.',
    'No downstream refresh or ML retraining is started.',
]


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        temp_path = Path(temp_name)
        if temp_path.exists():
            temp_path.unlink()


def build_module_closure_status(*, root: Path = ROOT, now: datetime | None = None) -> dict[str, Any]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    groups: list[dict[str, Any]] = []
    missing: list[str] = []
    total = 0
    present = 0
    for group_name, relative_paths in REQUIRED_COMPONENTS.items():
        rows = []
        for relative_path in relative_paths:
            total += 1
            exists = (root / relative_path).is_file()
            present += int(exists)
            if not exists:
                missing.append(relative_path)
            rows.append({'path': relative_path, 'present': exists})
        groups.append({
            'group': group_name,
            'required_count': len(relative_paths),
            'present_count': sum(1 for row in rows if row['present']),
            'complete': all(row['present'] for row in rows),
            'components': rows,
        })
    closed = not missing
    return {
        'step': '140',
        'name': 'Production Operations Final QA & Clean Module Closure',
        'module': MODULE_NAME,
        'step_range': STEP_RANGE,
        'generated_at_utc': current.isoformat(timespec='seconds'),
        'module_state': 'MODULE_CLOSED' if closed else 'CLOSURE_BLOCKED',
        'closure_ready': closed,
        'required_component_count': total,
        'present_component_count': present,
        'missing_component_count': len(missing),
        'missing_components': missing,
        'component_groups': groups,
        'read_only': True,
        'production_state_changed': False,
        'evidence_archives_modified': False,
        'registry_modified': False,
        'audit_logs_modified': False,
        'automatic_restore_performed': False,
        'downstream_refresh_started': False,
        'ml_retraining_started': False,
        'read_only_boundaries': list(READ_ONLY_BOUNDARIES),
        'next_module_required': False,
    }


def module_closure_markdown(status: dict[str, Any]) -> str:
    lines = [
        '# Step 140 — Production Operations Final QA & Clean Module Closure',
        '',
        f"- Module: **{status['module']}**",
        f"- Step range: **{status['step_range']}**",
        f"- Closure state: **{status['module_state']}**",
        f"- Components present: **{status['present_component_count']}/{status['required_component_count']}**",
        f"- Missing components: **{status['missing_component_count']}**",
        '',
        '## Component groups',
        '',
    ]
    for group in status['component_groups']:
        marker = 'PASS' if group['complete'] else 'BLOCKED'
        lines.append(f"- **{marker}** `{group['group']}` — {group['present_count']}/{group['required_count']}")
    lines.extend(['', '## Read-only closure boundaries', ''])
    lines.extend(f'- {item}' for item in status['read_only_boundaries'])
    if status['missing_components']:
        lines.extend(['', '## Missing components', ''])
        lines.extend(f'- `{item}`' for item in status['missing_components'])
    lines.extend([
        '',
        'The closure layer is diagnostic and documentary only. It does not perform production operations.',
        '',
    ])
    return '\n'.join(lines)


def write_module_closure_status(status: dict[str, Any]) -> None:
    payload = dict(status)
    payload['summary_md'] = module_closure_markdown(status)
    _atomic_write_text(STATUS_JSON, json.dumps(payload, ensure_ascii=False, indent=2))
    _atomic_write_text(SUMMARY_MD, payload['summary_md'])
