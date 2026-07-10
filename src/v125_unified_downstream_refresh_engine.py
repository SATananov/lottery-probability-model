from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / 'models' / 'v125_unified_downstream_refresh_status.json'
REPORT_JSON = ROOT / 'reports' / 'v125_unified_downstream_refresh_report.json'
SUMMARY_MD = ROOT / 'reports' / 'v125_unified_downstream_refresh_summary.md'
AUDIT_JSONL = ROOT / 'reports' / 'v125_unified_downstream_refresh_audit.jsonl'

PIPELINE = [
    {'id':'dataset_sync','name':'Historical / normalized / canonical','kind':'internal'},
    {'id':'r_statistics','name':'R statistical layer','kind':'powershell','command':['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','tools/run_r_statistics.ps1']},
    {'id':'r_features','name':'Step 121 R features','kind':'python','command':['tools/integrate_r_statistical_features.py','--all']},
    {'id':'decision','name':'Decision Center','kind':'python','command':['scripts/v115_build_play_decision_center.py']},
    {'id':'ticket_pack','name':'Real ticket pack','kind':'python','command':['scripts/v117_build_real_ticket_pack_builder.py']},
    {'id':'model_ticket_pack','name':'Model system ticket pack','kind':'python','command':['scripts/v118_build_model_system_ticket_builder.py']},
    {'id':'freshness','name':'Final freshness recheck','kind':'python','command':['tools/check_official_draw_freshness.py']},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _write(report: dict[str, Any]) -> None:
    for path in (STATUS_JSON, REPORT_JSON):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# Step 125 — Unified Downstream Refresh Pipeline','',f"- Status: **{report.get('status')}**",f"- Started: `{report.get('started_at_utc')}`",f"- Finished: `{report.get('finished_at_utc')}`",f"- Heavy ML retraining: **No**",'', '## Stages']
    for row in report.get('stages', []):
        lines.append(f"- {row.get('name')}: **{row.get('status')}** — {row.get('message','')}")
    SUMMARY_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    with AUDIT_JSONL.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + '\n')


def _run_command(stage: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    if stage['kind'] == 'python':
        cmd = [sys.executable, *stage['command']]
    else:
        executable = shutil.which(stage['command'][0])
        if not executable:
            return {'id':stage['id'],'name':stage['name'],'status':'manual_required','ok':False,'message':'PowerShell/R runner is unavailable.','output_tail':''}
        cmd = [executable, *stage['command'][1:]]
    try:
        done = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, encoding='utf-8', errors='replace', timeout=timeout_seconds)
        output = ((done.stdout or '') + ('\n' + done.stderr if done.stderr else '')).strip()
        return {'id':stage['id'],'name':stage['name'],'status':'ok' if done.returncode == 0 else 'failed','ok':done.returncode == 0,'message':'Completed.' if done.returncode == 0 else f'Exit code {done.returncode}.','output_tail':output[-3000:]}
    except subprocess.TimeoutExpired as exc:
        return {'id':stage['id'],'name':stage['name'],'status':'timeout','ok':False,'message':f'Timed out after {timeout_seconds}s.','output_tail':str(exc)[-3000:]}
    except Exception as exc:
        return {'id':stage['id'],'name':stage['name'],'status':'failed','ok':False,'message':str(exc),'output_tail':''}


def run_unified_downstream_refresh(*, plan_only: bool = False, timeout_seconds: int = 900, runner: Callable[[dict[str, Any], int], dict[str, Any]] | None = None, write_outputs: bool = True) -> dict[str, Any]:
    started = utc_now()
    stages: list[dict[str, Any]] = []
    blocked = False
    run_stage = runner or _run_command
    for stage in PIPELINE:
        if plan_only:
            stages.append({'id':stage['id'],'name':stage['name'],'status':'planned','ok':True,'message':'Ready to run.'})
            continue
        if blocked:
            stages.append({'id':stage['id'],'name':stage['name'],'status':'blocked','ok':False,'message':'Blocked by an earlier failed stage.'})
            continue
        if stage['kind'] == 'internal':
            try:
                from src.post_bst_model_data_refresh_engine import refresh_model_data_from_prize_history
                result = refresh_model_data_from_prize_history()
                ok = result.get('status_after', {}).get('status') == 'MODEL_DATA_SYNCED'
                row = {'id':stage['id'],'name':stage['name'],'status':'ok' if ok else 'failed','ok':ok,'message':result.get('status_after', {}).get('status','UNKNOWN'),'details':result}
            except Exception as exc:
                row = {'id':stage['id'],'name':stage['name'],'status':'failed','ok':False,'message':str(exc)}
        else:
            row = run_stage(stage, timeout_seconds)
        stages.append(row)
        if not row.get('ok'):
            blocked = True
    failed = [row for row in stages if not row.get('ok')]
    status = 'planned' if plan_only else ('completed' if not failed else 'check_required')
    report = {'step':'125','name':'Unified Downstream Refresh Pipeline','started_at_utc':started,'finished_at_utc':utc_now(),'status':status,'plan_only':plan_only,'heavy_ml_retraining_performed':False,'stages':stages,'failed_stage_count':len(failed)}
    if write_outputs:
        _write(report)
    return report
