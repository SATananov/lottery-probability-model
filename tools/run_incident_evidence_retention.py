from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v135_incident_evidence_retention_engine import (
    apply_archive_plan,
    apply_cleanup_plan,
    build_retention_plan,
    write_default_policy,
    write_retention_status,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='Preview or apply Step 135 incident evidence retention policy.')
    parser.add_argument('--archive-confirmation', help='Exact confirmation phrase for archiving eligible verified bundles.')
    parser.add_argument('--cleanup-confirmation', help='Exact confirmation phrase for deleting expired archived copies.')
    parser.add_argument('--write-status', action='store_true', help='Write status JSON and summary markdown.')
    args = parser.parse_args()

    write_default_policy()
    plan = build_retention_plan()
    if args.write_status:
        write_retention_status(plan)
    result: dict[str, object] = {'plan': plan}
    if args.archive_confirmation is not None:
        result['archive_result'] = apply_archive_plan(plan, confirmation=args.archive_confirmation)
        plan = build_retention_plan()
    if args.cleanup_confirmation is not None:
        result['cleanup_result'] = apply_cleanup_plan(plan, confirmation=args.cleanup_confirmation)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
