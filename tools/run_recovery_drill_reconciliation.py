from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.v137_recovery_drill_audit_reconciliation_engine import build_reconciliation_status, close_reconciliation_exception, write_reconciliation_status

def main()->None:
    p=argparse.ArgumentParser(description='Step 137 recovery drill reconciliation')
    p.add_argument('--write-status',action='store_true')
    p.add_argument('--close-exception')
    p.add_argument('--operator-note')
    p.add_argument('--confirmation')
    a=p.parse_args()
    status=build_reconciliation_status()
    if a.write_status: write_reconciliation_status(status)
    if a.close_exception:
        item=next((x for x in status['open_exceptions'] if x['exception_id']==a.close_exception),None)
        if item is None: raise SystemExit('Open exception not found.')
        event=close_reconciliation_exception(item,operator_note=a.operator_note or '',confirmation=a.confirmation or '')
        print(json.dumps(event,ensure_ascii=False,indent=2)); return
    print(json.dumps(status,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
