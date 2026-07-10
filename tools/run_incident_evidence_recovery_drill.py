from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.v136_incident_evidence_recovery_drill_engine import build_recovery_drill_plan, run_recovery_drill, write_recovery_drill_status

def main()->int:
    p=argparse.ArgumentParser(description='Preview or run Step 136 isolated evidence recovery drill.')
    p.add_argument('--archive')
    p.add_argument('--confirmation')
    p.add_argument('--retain-staging', action='store_true')
    args=p.parse_args()
    if not args.archive:
        print(json.dumps(build_recovery_drill_plan(),ensure_ascii=False,indent=2)); return 0
    result=run_recovery_drill(Path(args.archive),confirmation=args.confirmation or '',retain_staging_copy=args.retain_staging)
    write_recovery_drill_status(result)
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
