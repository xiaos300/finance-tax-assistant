"""D1 serial acceptance recorder. Missing real PG is blocked and exits 2."""
from pathlib import Path
import argparse
from datetime import datetime,timezone,timedelta
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/development/reports/2026-11-04_D1'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=OUT)
    args=parser.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    n=1
    while (out/f'attempt{n}').exists():n+=1
    run=out/f'attempt{n}';run.mkdir()
    env={**os.environ,'APP_ENV':'test','MODEL_MODE':'disabled','PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1','UV_CACHE_DIR':str(ROOT/'.cache/uv')}
    # Known actual configuration values are never copied into evidence.
    sys.path.insert(0,str(ROOT/'backend'))
    from app.core.config import configuration
    from sqlalchemy.engine import make_url
    values=configuration();secrets=[]
    for key,value in values.items():
        if not value:continue
        if key.endswith('_url') and 'database' in key:
            secrets.append(value)
            try:
                password=make_url(value).password
                if password:secrets.append(password)
            except Exception:pass
        if key in ('model_api_key','demo_u001_token','demo_u002_token'):secrets.append(value)
    def redact(s):
        for value in sorted(secrets,key=len,reverse=True):s=s.replace(value,'[REDACTED]')
        return s
    commands=[]
    def execute(label,argv,cwd=ROOT,expected=(0,)):
        p=subprocess.run([str(a) for a in argv],cwd=cwd,env=env,capture_output=True,encoding='utf-8',errors='replace')
        (run/(label+'.log')).write_text(redact(p.stdout+p.stderr),encoding='utf-8')
        commands.append(dict(label=label,command=[str(a) for a in argv],cwd=str(cwd.relative_to(ROOT)) or '.',exit_code=p.returncode,expected_exit_codes=list(expected),log=str((run/(label+'.log')).relative_to(out))))
        print(f'{label}: exit {p.returncode}',flush=True)
        return p.returncode
    uv=ROOT/'.tools/bin/uv.exe'
    lock_before={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'backend/uv.lock',ROOT/'frontend/package-lock.json')}
    frozen=execute('frozen-install',[uv,'sync','--frozen','--offline','--group','dev','--group','prepare'],ROOT/'backend')
    tests=execute('backend-tests',[uv,'run','--frozen','--no-sync','pytest','tests/unit','tests/integration','tests/api','--junitxml='+str(run/'pytest.xml'),'-q'],ROOT/'backend') if frozen==0 else 99
    execute('admin-preflight',[ROOT/'backend/.venv/Scripts/python.exe','-m','app.cli','inspect-admin'],ROOT/'backend',expected=(0,2))
    execute('test-maintenance-config',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/manage.ps1','-Action','InspectConfig','-TestTarget'],expected=(0,2))
    execute('test-maintenance-init',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/manage.ps1','-Action','Init','-TestTarget'],expected=(0,2))
    scan=execute('source-scan',[ROOT/'backend/.venv/Scripts/python.exe',ROOT/'scripts/verify_baseline.py','--output-dir',out])
    totals=dict(passed=0,failed=0,blocked=0,not_run=0)
    subitems=[]
    if (run/'pytest.xml').exists():
        xml=ET.parse(run/'pytest.xml')
        for case in xml.findall('.//testcase'):
            status='failed' if case.find('failure') is not None or case.find('error') is not None else 'blocked' if case.find('skipped') is not None else 'passed'
            totals[status]+=1
            subitems.append(dict(name=case.get('name'),file=case.get('classname'),status=status,
                case_ids=sorted(set(re.findall(r'TC\d{3}',case.get('name',''))))))
    else:totals['not_run']=1
    before=json.loads((OUT/'before.json').read_text(encoding='utf-8'))
    integrity=[dict(path=name,sha256=digest(ROOT/name),unchanged=digest(ROOT/name)==h) for name,h in before['protected_hashes'].items()]
    d0=json.loads((ROOT/'docs/development/reports/2026-11-03_D0_baseline/summary.json').read_text(encoding='utf-8'))
    historical_inputs=[dict(path=name,sha256=digest(ROOT/name),matches_D0_record=digest(ROOT/name)==h) for name,h in d0['protected_input_hashes'].items()]
    unchanged=all(x['unchanged'] for x in integrity) and all(x['matches_D0_record'] for x in historical_inputs)
    lock_after={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'backend/uv.lock',ROOT/'frontend/package-lock.json')}
    fail=tests!=0 or frozen!=0 or scan!=0 or not unchanged or lock_before!=lock_after
    state='failed' if fail else 'blocked' if totals['blocked'] else 'passed'
    mapping={c['id']:c for c in json.loads((ROOT/'docs/development/test-cases.json').read_text(encoding='utf-8'))['cases']}
    cases=[]
    for cid,scope in [('TC001','complete'),('TC002','complete'),('TC005','complete'),('TC006','complete'),('TC007','complete'),('TC009','deterministic_D1_only'),('TC011','deterministic_D1_only'),('TC027','deterministic_D1_only'),('TC013','read_permission_only'),('TC052','role_schema_guard_only')]:
        matching=[i for i in subitems if cid in i['case_ids']]
        real=[i for i in matching if '.unit.' not in i['file']]
        status='failed' if any(i['status']=='failed' for i in matching) else 'blocked' if any(i['status']=='blocked' for i in real) else 'passed' if real else 'not_run'
        cases.append(dict(case_id=cid,ac_refs=mapping[cid]['ac_refs'],scope=scope,status=status,whole_case_status=status if scope=='complete' else 'not_run',subitems=matching))
    seed=json.loads((ROOT/'data/seed/manifest.json').read_text(encoding='utf-8'))
    source=json.loads((out/'source-scan.json').read_text(encoding='utf-8')) if (out/'source-scan.json').exists() else {}
    result=dict(run_id='2026-11-04_D1_'+run.name,stage='D1',date=datetime.now(timezone(timedelta(hours=8))).isoformat(),
        requirements_version='1.3',contract_version='1.2 + approved deployment names 2026-11-04',model_mode='none',model_profile_id=None,
        fixture_id='B0/B1-direct-fixture/B2 (real PG execution blocked if skipped)',seed_hash=seed['normalized_hash'],
        test_target='finance_tax_test',test_counts=totals,d1_required_gate=state,
        gate_scope='Required serial PostgreSQL test suite; development preparation and final handoff remain separate',
        local_status='in_progress' if state=='passed' else state,external_status='not_applicable',
        overall_status='blocked_external' if state=='blocked' else 'in_progress' if state=='passed' else state,development_preparation='not_run: requires passed real test gate',
        source_tree_hash=source.get('source_tree_hash'),runtime_versions={name:importlib.metadata.version(name) for name in ('sqlalchemy','psycopg','alembic','pydantic','fastapi','pytest')},
        command='backend/.venv/Scripts/python.exe scripts/verify_d1.py',exit_code=1 if fail else 2 if state=='blocked' else 0,
        lock_hashes=lock_after,locks_unchanged=lock_before==lock_after,protected_inputs=integrity,protected_inputs_against_D0=historical_inputs,
        protected_inputs_unchanged=unchanged,case_results=cases,subitems=subitems,
        not_run=['TC052 D6 restore branch','D2 and later stages','Development database bootstrap/migration/seed/grant'],
        evidence_paths=[str(run.relative_to(out))+'/commands.json',str(run.relative_to(out))+'/pytest.xml','source-scan.json'])
    (run/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for path in (run/'summary.json',out/'summary.json'):path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':state,'counts':totals,'exit_code':result['exit_code']},ensure_ascii=False))
    return result['exit_code']


if __name__=='__main__':raise SystemExit(main())
