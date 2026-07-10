from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v133_incident_evidence_integrity_engine import inspect_incident_evidence_zip
from src.v134_incident_evidence_registry_engine import (
    load_registry_events,
    rebuild_registry_status,
    register_verification_result,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect registry history or verify and register an incident evidence ZIP.')
    parser.add_argument('--verify', type=Path, help='Step 132 evidence ZIP to inspect and register.')
    parser.add_argument('--history', action='store_true', help='Print current registry status.')
    args = parser.parse_args()

    if args.verify:
        if not args.verify.is_file():
            parser.error(f'Archive not found: {args.verify}')
        result = inspect_incident_evidence_zip(args.verify.read_bytes(), source_name=args.verify.name)
        event = register_verification_result(result)
        print(json.dumps({'event': event, 'verdict': result['verdict']}, ensure_ascii=False, indent=2))
        return 0 if result['verdict'] == 'verified' else 2

    status = rebuild_registry_status(write_outputs=False)
    if args.history:
        status['events'] = load_registry_events()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
