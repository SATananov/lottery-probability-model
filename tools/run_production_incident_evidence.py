from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v132_production_incident_evidence_engine import build_incident_evidence, write_incident_evidence_export


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a read-only Step 132 production incident evidence bundle.')
    parser.add_argument('--live-bst-check', action='store_true')
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()

    evidence = build_incident_evidence(
        live_bst_check=args.live_bst_check,
        timeout_seconds=max(1, args.timeout),
        write_outputs=True,
    )
    export_path = write_incident_evidence_export(evidence)
    print(f"STEP_132_EVIDENCE_OK bundle_id={evidence['bundle_id']} export={export_path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
