from __future__ import annotations
import json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.v138_recovery_exception_sla_engine import ACK_CONFIRMATION, build_exception_follow_up_queue, record_follow_up_event

def main()->None:
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); audit=root/'followup.jsonl'
        reconciliation={
            'rows':[
                {'exception_id':'EXC-CRIT','bundle_id':'INC-1','drill_id':'D1','completed_at_utc':'2026-07-10T00:00:00+00:00','exception_codes':['PRODUCTION_STATE_CHANGED'],'reconciliation_status':'OPEN_EXCEPTION'},
                {'exception_id':'EXC-HIGH','bundle_id':'INC-2','drill_id':'D2','completed_at_utc':'2026-07-09T00:00:00+00:00','exception_codes':['STAGING_SHA_MISMATCH'],'reconciliation_status':'OPEN_EXCEPTION'},
                {'exception_id':'EXC-CLOSED','bundle_id':'INC-3','drill_id':'D3','completed_at_utc':'2026-07-01T00:00:00+00:00','exception_codes':['REGISTRY_RECORD_MISSING'],'reconciliation_status':'CLOSED_EXCEPTION'},
            ]
        }
        now=datetime(2026,7,10,6,0,0,tzinfo=timezone.utc)
        status=build_exception_follow_up_queue(now=now,reconciliation_status=reconciliation,follow_up_audit_path=audit)
        assert status['open_count']==2 and status['overdue_count']==2 and status['critical_count']==1
        crit=next(x for x in status['action_queue'] if x['exception_id']=='EXC-CRIT')
        try:
            record_follow_up_event(crit,operator_note='sufficient note',confirmation='wrong',follow_up_audit_path=audit)
            raise AssertionError('Wrong confirmation accepted')
        except PermissionError: pass
        before=json.dumps(reconciliation,sort_keys=True)
        event=record_follow_up_event(crit,operator_note='Escalated to the responsible operator for immediate review.',confirmation=ACK_CONFIRMATION,follow_up_audit_path=audit)
        assert event['event_type']=='ESCALATION_ACKNOWLEDGED'
        assert json.dumps(reconciliation,sort_keys=True)==before
        status2=build_exception_follow_up_queue(now=now,reconciliation_status=reconciliation,follow_up_audit_path=audit)
        row=next(x for x in status2['rows'] if x['exception_id']=='EXC-CRIT')
        assert row['latest_follow_up_event']=='ESCALATION_ACKNOWLEDGED'
        assert row['reconciliation_status']=='OPEN_EXCEPTION'
    print('STEP_138_VERIFY_OK')
if __name__=='__main__': main()
