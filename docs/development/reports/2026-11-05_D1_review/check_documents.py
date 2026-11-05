"""Run from project root; validate this review's Markdown references only."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
import sys,re,json,subprocess
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'scripts'))
from verify_d1_handoff import prose,anchors
OUT=ROOT/'docs/development/reports/2026-11-05_D1_review'
names=['Documentation.md','docs/development/progress.md','docs/development/reports/2026-11-05_D1_review.md']
links=[];errors=[]
for name in names:
    p=ROOT/name;body,fence=prose(p.read_text(encoding='utf-8-sig'))
    if fence:errors.append(dict(source=name,error='unclosed fence'))
    body=re.sub(r'`+[^`\n]*`+','',body)
    for m in re.finditer(r'(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)',body):
        label,dest=m.groups();u=urlsplit(dest.strip().strip('<>'))
        if u.scheme or u.netloc:continue
        target=(p.parent/unquote(u.path)).resolve() if u.path else p.resolve()
        item=dict(source=name,target=str(target.relative_to(ROOT)).replace('\\','/'),fragment=unquote(u.fragment))
        if not target.exists():item['error']='missing file'
        elif u.fragment and (target.suffix!='.md' or unquote(u.fragment) not in anchors(target)):
            item['error']='missing heading anchor'
        if 'error' in item:errors.append(item)
        links.append(item)
argv=['git','diff','--check']
p=subprocess.run(argv,capture_output=True,encoding='utf-8',errors='replace')
result=dict(date='2026-11-05',scope=names,command='backend/.venv/Scripts/python.exe docs/development/reports/2026-11-05_D1_review/check_documents.py',cwd='.',links_checked=len(links),anchors_checked=sum(bool(x['fragment']) for x in links),links=links,errors=errors,diff_check=dict(command=argv,exit_code=p.returncode),manual_trace=dict(status='reviewed',items=['D1 task card gate vs case_results and JUnit','Current code vs recorded source fingerprints','D2 prerequisite and separate live gate','Historical acceptance is not a new test run','D2 not started and next-round authorization prompt']),limitations=['No external links or browser rendering checked','Static links do not prove business acceptance','Historical SQL/log whitespace exceptions recorded separately'])
result['exit_code']=1 if errors or p.returncode else 0
(OUT/'document-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('links_checked','anchors_checked','errors','exit_code')},ensure_ascii=False))
sys.exit(result['exit_code'])
