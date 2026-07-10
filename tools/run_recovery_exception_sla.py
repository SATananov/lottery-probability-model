from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.v138_recovery_exception_sla_engine import build_exception_follow_up_queue, record_follow_up_event, write_exception_follow_up_status

def main()->None:
    p=argparse.ArgumentParser(description='Step 138 recovery exception SLA and follow-up queue')
    p.add_argument('--write-status',action='store_true')
    p.add_argument('--acknowledge')
    p.add_argument('--operator-note')
    p.add_argument('--confirmation')
    a=p.parse_args()
    status=build_exception_follow_up_queue()
    if a.write_status: write_exception_follow_up_status(status)
    if a.acknowledge:
        item=next((x for x in status['action_queue'] if x['exception_id']==a.acknowledge),None)
        if item is None: raise SystemExit('Open exception not found in follow-up queue.')
        event=record_follow_up_event(item,operator_note=a.operator_note or '',confirmation=a.confirmation or '')
        print(json.dumps(event,ensure_ascii=False,indent=2)); return
    print(json.dumps(status,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
