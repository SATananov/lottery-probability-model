from __future__ import annotations
import json, sys, tempfile, zipfile, io, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.v136_incident_evidence_recovery_drill_engine import DRILL_CONFIRMATION, build_recovery_drill_plan, run_recovery_drill

def make_bundle(bundle_id:str)->bytes:
    evidence={'bundle_id':bundle_id,'read_only':True,'production_state_changed':False,'operations_snapshot':{'checks':{}}}
    files={'incident_evidence.json':json.dumps(evidence).encode(),'operator_summary.md':b'ok','operational_checks.json':b'{}'}
    manifest={'bundle_id':bundle_id,'created_at_utc':'2026-07-10T00:00:00+00:00','files':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()}}
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in files.items(): z.writestr(k,v)
        z.writestr('manifest.json',json.dumps(manifest).encode())
    return out.getvalue()

def main()->None:
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); archive=root/'archive'; archive.mkdir(); registry=root/'registry.jsonl'; staging=root/'staging'; audit=root/'audit.jsonl'
        bid='INC-RECOVERY-TEST'; path=archive/f'{bid}.zip'; data=make_bundle(bid); path.write_bytes(data); sha=hashlib.sha256(data).hexdigest()
        registry.write_text(json.dumps({'event_type':'VERIFIED','bundle_id':bid,'recorded_at_utc':'2026-07-10T00:00:00+00:00','archive_sha256':sha,'source_name':path.name,'verdict':'verified'})+'\n',encoding='utf-8')
        before=path.read_bytes(); reg_before=registry.read_bytes()
        plan=build_recovery_drill_plan(archive_dir=archive,registry_path=registry)
        assert plan['eligible_count']==1 and plan['production_state_changed'] is False
        try:
            run_recovery_drill(path,confirmation='wrong',registry_path=registry,staging_root=staging,audit_path=audit)
            raise AssertionError('Wrong confirmation accepted')
        except PermissionError: pass
        result=run_recovery_drill(path,confirmation=DRILL_CONFIRMATION,registry_path=registry,staging_root=staging,audit_path=audit)
        assert result['drill_verdict']=='passed'
        assert result['automatic_production_restore_performed'] is False
        assert path.read_bytes()==before and registry.read_bytes()==reg_before
        assert not any(staging.iterdir())
    print('STEP_136_VERIFY_OK')
if __name__=='__main__': main()
