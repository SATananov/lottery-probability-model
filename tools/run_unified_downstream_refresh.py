from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.v125_unified_downstream_refresh_engine import run_unified_downstream_refresh

def main() -> int:
    parser = argparse.ArgumentParser(description='Step 125 unified downstream refresh pipeline')
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    report = run_unified_downstream_refresh(plan_only=args.plan, timeout_seconds=args.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] in {'planned','completed'} else 2
if __name__ == '__main__':
    raise SystemExit(main())
