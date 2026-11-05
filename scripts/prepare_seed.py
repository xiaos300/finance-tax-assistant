"""Read-only official source conversion. Never use the explanation sheet's totals."""
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(value).hexdigest()


def cents(value):
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d < 0 or d * 100 != (d * 100).to_integral_value() or d * 100 > 2**63-1:
            raise ValueError()
        return int(d * 100)
    except (InvalidOperation, ValueError):
        raise ValueError('Invalid source monetary value; finite nonnegative BIGINT cents required.') from None


def prepare():
    book = ROOT/'materials/02_示例数据.xlsx'
    rules_source = ROOT/'materials/03_业务规则.docx'
    wb = load_workbook(book, read_only=True, data_only=False)
    business = dict(dataset_id='official-1.1.0', companies=[], users=[], permissions=[], invoices=[], bank_transactions=[])
    for rownum, row in enumerate(wb['企业与用户'].values, 1):
        if row[0] in ('C001','C002'):
            business['companies'].append(dict(zip(('company_id','name','short_name'), row[:3]),source_ref=f'企业与用户!{rownum}'))
        if row[0] in ('U001','U002'):
            business['users'].append(dict(user_id=row[0],name=row[1],source_ref=f'企业与用户!{rownum}'))
            for cid, cell in zip(('C001','C002'), row[2:4]):
                if cell not in ('可查看并修改','仅查看','无权访问'):raise ValueError('Unknown source permission')
                business['permissions'].append(dict(user_id=row[0],company_id=cid,can_read=cell!='无权访问',can_write=cell=='可查看并修改',source_ref=f'企业与用户!{rownum}'))
    for sheet, key, fields in [
        ('发票','invoices',('company_id','invoice_id','invoice_date','seller','item_name','amount_cents','purpose','note')),
        ('银行流水','bank_transactions',('company_id','transaction_id','transaction_date','direction','amount_cents','counterparty','note'))]:
        for rownum, row in enumerate(wb[sheet].values, 1):
            if row[0] not in ('C001','C002'): continue
            item = dict(zip(fields,row))
            date_key = 'invoice_date' if key=='invoices' else 'transaction_date'
            if not isinstance(item[date_key], datetime):raise ValueError(f'{sheet}!{rownum}: invalid date')
            item[date_key] = item[date_key].date().isoformat()
            item['amount_cents'] = cents(item['amount_cents'])
            if key=='bank_transactions':
                item['direction'] = {'收入':'income','支出':'expense'}[item['direction']]
                if item['amount_cents']==0:raise ValueError('Bank amount must be positive')
            item['source_ref'] = f'{sheet}!{rownum}'
            business[key].append(item)
    wb.close()
    with ZipFile(rules_source) as archive:
        root=ET.fromstring(archive.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs=[''.join(p.itertext()) for p in root.findall('.//w:p',ns)]
    heading=re.compile(r'^(R00[1-4]) (.+?) ([12]\.0)版(?: 已停用)?$')
    groups=[]
    for i,p in enumerate(paragraphs):
        m=heading.match(p)
        if m: groups.append((i,m.groups()))
    policies=[('amount',['C001','C002'],'2026-01-01','enabled',{'kind':'independent_totals'}),
        ('purpose',['C001'],'2026-08-01','disabled',{'kind':'amount_gte','threshold_cents':100000}),
        ('purpose',['C001'],'2026-09-01','enabled',{'kind':'all'}),
        ('purpose',['C002'],'2026-08-01','enabled',{'kind':'amount_gte','threshold_cents':100000}),
        ('bank',['C001','C002'],'2026-01-01','enabled',{'kind':'bank_readonly'})]
    if len(groups)!=5:raise ValueError('Expected five explicit source rule headings')
    rules=[]
    for n,((i,(rid,name,version)),(topic,companies,effective,status,policy)) in enumerate(zip(groups,policies)):
        end=groups[n+1][0] if n+1<len(groups) else len(paragraphs)
        rules.append(dict(rule_id=rid,version=version,name=name,topic=topic,company_ids=companies,
            effective_from=effective,status=status,body='\n'.join(paragraphs[i+1:end]).strip(),policy=policy,
            source_ref=f'materials/03_业务规则.docx::{paragraphs[i]}'))
    normalized_rules={'dataset_id':business['dataset_id'],'rules':rules}
    for key in ('companies','users','permissions','invoices','bank_transactions'):
        business[key].sort(key=lambda r:canonical(r))
    if [len(business[k]) for k in ('companies','users','permissions','invoices','bank_transactions')]!=[2,2,4,40,48]:
        raise ValueError('Source count mismatch')
    # Independent conversion check; no runtime code imports these expectations.
    totals={}
    for cid in ('C001','C002'):
        for month in ('2026-08','2026-09'):
            rows=[r for r in business['invoices'] if r['company_id']==cid and r['invoice_date'].startswith(month)]
            bank=[r for r in business['bank_transactions'] if r['company_id']==cid and r['transaction_date'].startswith(month)]
            totals[cid+'/'+month]=[sum(r['amount_cents'] for r in rows)]+[sum(r['amount_cents'] for r in bank if r['direction']==d) for d in ('expense','income')]
    expected=[[904635,572099,1485075],[962206,718074,1300050],[1366705,934110,1880025],[1266724,808724,1370075]]
    if list(totals.values())!=expected:raise ValueError('Detail totals do not reconcile')
    dest=ROOT/'data/seed';dest.mkdir(parents=True,exist_ok=True)
    normalized_hash=sha(canonical([business,normalized_rules]).encode())
    manifest=dict(dataset_id=business['dataset_id'],schema_revision='0001',normalized_hash=normalized_hash,
        source_hashes={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes()) for p in (book,rules_source)},
        lineage='Per-row source_ref in business.json; exact heading and body in rules.json; explanation sheet excluded.',
        validation=dict(counts=dict(companies=2,users=2,permissions=4,invoices=40,bank_transactions=48,rules=5),totals_cents=totals))
    for name,data in [('business',business),('rules',normalized_rules),('manifest',manifest)]:
        (dest/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'normalized_hash':normalized_hash,'validation':manifest['validation']},ensure_ascii=False))


if __name__=='__main__':prepare()
