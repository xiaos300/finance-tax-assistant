from pathlib import Path
import sys,json,hashlib,subprocess,re,xml.etree.ElementTree as ET
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT/'scripts'))
from verify_d1_handoff import prose,anchors
OUT=ROOT/'docs/development/reports/2026-11-05_D1_review'
E=ROOT/'docs/development/reports/2026-11-05_D1_credentials'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=read(E/'source-scan.json')['files']
fingerprints=[]
for name,h in source.items():
    if name.startswith(('backend/','frontend/','scripts/','data/seed/','deploy/')):
        p=ROOT/name
        fingerprints.append(dict(path=name,matches=p.exists() and digest(p)==h))
summary=read(E/'summary.json')
protected=[dict(path=x['path'],matches=digest(ROOT/x['path'])==x['sha256']) for x in summary['protected_inputs']]
cases=ET.parse(E/'attempt1/pytest.xml').findall('.//testcase')
counts=dict(total=len(cases),failed=sum(c.find('failure') is not None or c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
commands=read(E/'attempt1/commands.json')
command_checks=[dict(label=x['label'],exit_code=x['exit_code'],expected=x['exit_code'] in x['expected_exit_codes'],log_exists=(E/x['log']).exists()) for x in commands]
http=read(E/'development-http.json')['checks']
http_ok=all(x['actual_status']==x['expected_status'] and x['request_id_matches'] for x in http)
paths=subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z']).decode('utf-8').split('\0')
paths=sorted(set(p for p in paths if p and not p.startswith(('note.assets/','docs/development/reports/2026-11-05_D1_review/'))))
# Scan all candidate text, including historical evidence; output locations only.
rules={
 'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'provider_key':r'\bsk-[A-Za-z0-9_-]{24,}\b',
 'credential_url':r'postgres(?:ql)?(?:\+psycopg)?://[^\s/:]+:[^\s@]+@',
 'bearer':r'Bearer\s+[A-Za-z0-9_-]{24,}',
}
findings=[];placeholders=[]
for name in paths:
    p=ROOT/name
    if not p.is_file():continue
    try:body=p.read_text(encoding='utf-8-sig')
    except UnicodeError:continue
    for n,line in enumerate(body.splitlines(),1):
        for rule,pattern in rules.items():
            if re.search(pattern,line):
                item=dict(path=name,line=n,rule=rule)
                if rule=='credential_url' and ':<URL编码密码>@' in line:
                    placeholders.append(item)
                else:findings.append(item)
result=dict(date='2026-11-05',method='Read-only evidence audit; no database, model or business tests rerun',source_fingerprints=fingerprints,protected_inputs=protected,junit=counts,commands=command_checks,http_checks=len(http),http_passed=http_ok,secret_pattern_findings=findings,manually_reviewed_password_placeholders=placeholders,excluded=['note.assets/ (pre-existing unrelated image)'],candidate_files=paths,case_gates=summary.get('case_results',[]))
result['passed']=all(x['matches'] for x in fingerprints+protected) and counts==dict(total=216,failed=0,skipped=0) and all(x['expected'] and x['log_exists'] for x in command_checks) and http_ok and not findings
(OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=result['passed'],fingerprints=len(fingerprints),mismatches=[x for x in fingerprints if not x['matches']],protected=len(protected),junit=counts,http=len(http),findings=findings,candidates=len(paths)),ensure_ascii=False))
sys.exit(0 if result['passed'] else 1)
