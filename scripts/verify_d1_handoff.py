"""Static D1 Markdown/protected-input handoff checks, separate from business tests."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
import hashlib
import json
import re
import subprocess
import sys
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/development/reports/2026-11-04_D1'
FILES=['AGENTS.md','Documentation.md','Plan.md','README.md',
    'docs/architecture/05_数据库与数据架构设计.md','docs/architecture/06_API接口设计.md',
    'docs/architecture/08_非功能架构设计.md','docs/architecture/09_工程目录结构设计.md',
    'docs/architecture/10_部署与运行架构设计.md','docs/architecture/12_开发实施契约补充.md',
    'docs/development/00_开发导航.md','docs/development/02_开发实施总计划.md',
    'docs/development/04_测试与验收规范.md','docs/development/tasks/D1_PostgreSQL与只读业务.md',
    'docs/development/progress.md','docs/development/reports/2026-11-04_D1.md']


def prose(s):
    result=[];fence=None
    for line in s.splitlines():
        m=re.match(r'^\s{0,3}(`{3,}|~{3,})',line)
        if m:
            mark=m.group(1)
            if fence is None:fence=mark
            elif mark[0]==fence[0] and len(mark)>=len(fence):fence=None
        elif fence is None:result.append(line)
    return '\n'.join(result),fence


def anchors(path):
    s,_=prose(path.read_text(encoding='utf-8-sig'));seen={}
    for line in s.splitlines():
        m=re.match(r'^ {0,3}#{1,6}\s+(.+?)\s*#*$',line)
        if not m:continue
        title=m.group(1)
        plain=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).replace('`','')
        slug=''.join(c for c in plain.lower() if c in '_- ' or unicodedata.category(c)[0] in 'LNM').replace(' ','-')
        candidate=slug;n=0
        while candidate in seen:n+=1;candidate=f'{slug}-{n}'
        seen[candidate]=title
    for value in re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)',s):seen[value]='explicit HTML anchor'
    return seen


def main():
    links=[];errors=[]
    for name in FILES:
        p=ROOT/name
        body,fence=prose(p.read_text(encoding='utf-8-sig'))
        if fence:errors.append(dict(source=name,error='unclosed fence'))
        body=re.sub(r'`+[^`\n]*`+','',body)
        for m in re.finditer(r'(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)',body):
            label,dest=m.groups();u=urlsplit(dest.strip().strip('<>'))
            if u.scheme or u.netloc:continue
            target=(p.parent/unquote(u.path)).resolve() if u.path else p.resolve()
            try:relative=target.relative_to(ROOT).as_posix()
            except ValueError:relative=str(target);errors.append(dict(source=name,error='outside workspace',target=relative));continue
            item=dict(source=name,label=label,target=relative,fragment=unquote(u.fragment))
            if not target.exists():item['error']='missing file'
            elif u.fragment:
                if target.suffix.lower()!='.md':item['error']='non-Markdown fragment'
                elif unquote(u.fragment) not in anchors(target):item['error']='missing heading anchor'
                else:item['heading']=anchors(target)[unquote(u.fragment)]
            if 'error' in item:errors.append(item)
            links.append(item)
    checks=[]
    for label,argv in [('compile-python',[sys.executable,'-m','compileall','-q','backend/app','backend/tests','backend/migrations','scripts']),
                       ('git-diff-check',['git','diff','--check'])]:
        p=subprocess.run(argv,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace')
        (OUT/(label+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
        checks.append(dict(command=argv,cwd='.',exit_code=p.returncode,log=label+'.log'))
    integrity=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    raw=Path(ROOT/'README.md').read_text(encoding='utf-8')
    cli=Path(ROOT/'backend/app/cli.py').read_text(encoding='utf-8')
    ps=Path(ROOT/'scripts/manage.ps1').read_text(encoding='utf-8')
    actions=['InspectAdmin','BootstrapTest','BootstrapDev','InspectConfig','Init','Seed','GrantRuntime','Inspect','ResetTest']
    consistency={action:action in raw and action in ps for action in actions}
    env_lines=(ROOT/'.env.example').read_text(encoding='utf-8').splitlines()
    names=['DATABASE_URL','MIGRATION_DATABASE_URL','TEST_DATABASE_URL','TEST_MIGRATION_DATABASE_URL','ADMIN_DATABASE_URL','DEMO_U001_TOKEN','DEMO_U002_TOKEN']
    consistency.update({name: name in raw and name+'=' in env_lines for name in names})
    contracts={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
        'docs/architecture/contracts/contracts.schema.json','docs/architecture/contracts/tools.json','docs/architecture/contracts/http-operations.json')}
    result=dict(scope=FILES,method='Resolve local relative file links, Markdown headings with duplicate suffixes and explicit anchors; exclude fenced code/inline examples. GitHub/VS Code punctuation rules applied to actual headings read from targets.',
        limitations=['No external URL or browser rendering validation','JSON/code/log evidence uses file links; no pseudo JSON Pointer anchors','Link existence cannot prove PostgreSQL or AI success'],
        links_checked=len(links),anchors_checked=sum(bool(i['fragment']) for i in links),links=links,errors=errors,
        commands=checks,readme_config_script_consistency=consistency,machine_contract_hashes=contracts,
        protected_input_checks=integrity['protected_inputs'],protected_inputs_against_D0=integrity['protected_inputs_against_D0'],
        manual_trace=dict(status='reviewed',scope=['Implementation statements link source and tests','Passed statements link actual logs/JUnit; skipped PG remains blocked','Unchanged claims link hash comparisons','D1 gate and no D2 progression are explicit','README native target restrictions, credentials, actions and stop/failure behavior match source'],
            business_acceptance='blocked; manual trace review is not a business pass'))
    code=1 if errors or any(c['exit_code'] for c in checks) or not all(consistency.values()) or not integrity['protected_inputs_unchanged'] else 0
    result['exit_code']=code
    (OUT/'handoff-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('links_checked','anchors_checked','errors','readme_config_script_consistency','exit_code')},ensure_ascii=False))
    return code


if __name__=='__main__':raise SystemExit(main())
