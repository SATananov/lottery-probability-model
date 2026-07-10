from __future__ import annotations
import py_compile, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.v125_unified_downstream_refresh_engine import PIPELINE, run_unified_downstream_refresh

def fake_runner(stage, timeout):
    return {'id':stage['id'],'name':stage['name'],'status':'ok','ok':True,'message':'simulated','output_tail':''}

def main() -> int:
    files = [ROOT/'src/v125_unified_downstream_refresh_engine.py',ROOT/'src/v125_unified_downstream_refresh_section.py',ROOT/'tools/run_unified_downstream_refresh.py']
    for path in files: py_compile.compile(str(path), doraise=True)
    plan = run_unified_downstream_refresh(plan_only=True, write_outputs=False)
    assert plan['status'] == 'planned' and len(plan['stages']) == len(PIPELINE)
    simulated = run_unified_downstream_refresh(runner=fake_runner, write_outputs=False)
    assert simulated['status'] == 'completed', simulated
    calls=[]
    def fail_second(stage, timeout):
        calls.append(stage['id'])
        ok = stage['id'] != 'r_features'
        return {'id':stage['id'],'name':stage['name'],'status':'ok' if ok else 'failed','ok':ok,'message':'test','output_tail':''}
    failed = run_unified_downstream_refresh(runner=fail_second, write_outputs=False)
    assert failed['status'] == 'check_required'
    assert any(x['status']=='blocked' for x in failed['stages'])
    assert simulated['heavy_ml_retraining_performed'] is False
    print('STEP_125_VERIFY_OK')
    return 0
if __name__ == '__main__': raise SystemExit(main())
