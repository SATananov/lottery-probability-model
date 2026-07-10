from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v133_incident_evidence_integrity_engine import inspect_incident_evidence_zip


def main() -> int:
    parser = argparse.ArgumentParser(description='Verify a Step 132 incident evidence ZIP.')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--write-outputs', action='store_true')
    args = parser.parse_args()
    if not args.archive.is_file():
        parser.error(f'Archive not found: {args.archive}')
    result = inspect_incident_evidence_zip(
        args.archive.read_bytes(),
        source_name=args.archive.name,
        write_outputs=args.write_outputs,
    )
    print(json.dumps({
        'verdict': result['verdict'],
        'bundle_id': result.get('bundle_id'),
        'archive_sha256': result['archive_sha256'],
        'failed_check_count': result['failed_check_count'],
    }, ensure_ascii=False, indent=2))
    return 0 if result['verdict'] == 'verified' else 2


if __name__ == '__main__':
    raise SystemExit(main())
