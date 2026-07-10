from __future__ import annotations
import hashlib, json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.v137_recovery_drill_audit_reconciliation_engine import CLOSE_CONFIRMATION, build_reconciliation_status, close_reconciliation_exception

def main()->None:
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); drills=root/'drills.jsonl'; registry=root/'registry.jsonl'; closures=root/'closures.jsonl'
        sha=hashlib.sha256(b'x').hexdigest(); bid='INC-137-TEST'
        registry.write_text(json.dumps({'bundle_id':bid,'event_type':'VERIFIED','verdict':'verified','archive_sha256':sha,'recorded_at_utc':'2026-07-10T00:00:00+00:00'})+'\n',encoding='utf-8')
        good={'drill_id':'DRILL-GOOD','bundle_id':bid,'completed_at_utc':'2026-07-10T01:00:00+00:00','source_sha256':sha,'staged_sha256':sha,'drill_verdict':'passed','integrity_verdict':'verified','automatic_production_restore_performed':False,'production_state_changed':False}
        bad=dict(good,drill_id='DRILL-BAD',staged_sha256='bad',drill_verdict='failed')
        drills.write_text(json.dumps(good)+'\n'+json.dumps(bad)+'\n',encoding='utf-8')
        status=build_reconciliation_status(drill_audit_path=drills,registry_path=registry,closure_audit_path=closures)
        assert status['reconciled_count']==1 and status['open_exception_count']==1
        exc=status['open_exceptions'][0]
        try:
            close_reconciliation_exception(exc,operator_note='sufficient note',confirmation='wrong',closure_audit_path=closures)
            raise AssertionError('Wrong confirmation accepted')
        except PermissionError: pass
        before_registry=registry.read_bytes(); before_drills=drills.read_bytes()
        close_reconciliation_exception(exc,operator_note='Reviewed and accepted for documented operational reasons.',confirmation=CLOSE_CONFIRMATION,closure_audit_path=closures)
        status2=build_reconciliation_status(drill_audit_path=drills,registry_path=registry,closure_audit_path=closures)
        assert status2['open_exception_count']==0 and status2['closed_exception_count']==1
        assert registry.read_bytes()==before_registry and drills.read_bytes()==before_drills
    print('STEP_137_VERIFY_OK')
if __name__=='__main__': main()
