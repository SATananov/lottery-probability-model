from __future__ import annotations

import io
import json
import zipfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v132_production_incident_evidence_engine import build_incident_evidence, build_incident_evidence_zip


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    evidence = build_incident_evidence(live_bst_check=False, write_outputs=False)
    require(evidence['step'] == '132', 'wrong step')
    require(evidence['read_only'] is True, 'bundle must be read-only')
    require(evidence['secrets_redacted'] is True, 'redaction flag missing')
    require(evidence['production_state_changed'] is False, 'production mutation detected')
    require(evidence['heavy_ml_retraining_performed'] is False, 'heavy ML retraining detected')
    require(str(evidence['bundle_id']).startswith('INC-'), 'invalid bundle id')
    require(len(evidence['file_fingerprints']) >= 5, 'missing file fingerprints')

    archive_bytes = build_incident_evidence_zip(evidence)
    require(len(archive_bytes) > 0, 'empty ZIP')
    with zipfile.ZipFile(io.BytesIO(archive_bytes), 'r') as archive:
        names = set(archive.namelist())
        require(names == {'incident_evidence.json', 'operator_summary.md', 'operational_checks.json', 'manifest.json'}, 'unexpected ZIP contents')
        payload = archive.read('incident_evidence.json').decode('utf-8')
        parsed = json.loads(payload)
        require(parsed['bundle_id'] == evidence['bundle_id'], 'bundle mismatch')
        require('[REDACTED]' in payload or 'token_value' not in payload, 'sensitive token value exposed')
        require(archive.testzip() is None, 'corrupt ZIP entry')

    section = (ROOT / 'src' / 'v131_production_operations_dashboard_section.py').read_text(encoding='utf-8')
    require('Incident evidence' in section, 'dashboard tab missing')
    require('render_v132_production_incident_evidence_section' in section, 'Step 132 section not wired')
    print('STEP_132_VERIFY_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
