import json
from pathlib import Path
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator,FormatChecker
import pytest
from sqlalchemy.exc import OperationalError
from app.api.dependencies import ledger_service

ROOT=Path(__file__).resolve().parents[3]
SCHEMA=json.loads((ROOT/'docs/architecture/contracts/contracts.schema.json').read_text(encoding='utf-8'))


def validate(name,payload):
    Draft202012Validator({'$ref':'#/$defs/'+name,'$defs':SCHEMA['$defs']},format_checker=FormatChecker()).validate(payload)


@pytest.fixture
def client(pg,monkeypatch):
    monkeypatch.setenv('MODEL_MODE','disabled')
    monkeypatch.setenv('DEMO_U001_TOKEN','TC013_SYNTHETIC_U001_TOKEN_0000000000')
    monkeypatch.setenv('DEMO_U002_TOKEN','TC013_SYNTHETIC_U002_TOKEN_0000000000')
    from app.main import create_app
    app=create_app();app.dependency_overrides[ledger_service]=lambda:pg[2]
    with TestClient(app) as c:yield c


def headers(user='U001'):return {'Authorization':f'Bearer TC013_SYNTHETIC_{user}_TOKEN_0000000000'}


@pytest.mark.parametrize('path,schema',[
    ('/me','Principal'),('/invoices/search?limit=3','InvoicePage'),('/companies/C001/invoices/F002','Invoice'),
    ('/companies/C001/bank-transactions?business_month=2026-09&limit=3','BankPage'),
    ('/companies/C001/totals?business_month=2026-09','Totals'),
    ('/companies/C001/totals?business_month=2026-09&metrics=invoice_total','Totals'),
    ('/companies/C001/purpose-check?business_month=2026-09','Check'),
    ('/companies/C001/rules?business_month=2026-09&topic=purpose','RuleResolution')])
def test_TC001_D1_HTTP_schema(client,path,schema):
    response=client.get('/api/v1'+path,headers=headers())
    assert response.status_code==200
    assert response.headers['x-request-id']==response.json()['request_id']
    validate(schema,response.json()['data'])


def test_TC013_identity_and_company_acl(client):
    for user,companies in [('U001',['C001','C002']),('U002',['C001'])]:
        r=client.get('/api/v1/me',headers={**headers(user),'X-User-ID':'U001' if user=='U002' else 'U002'})
        assert r.json()['data']['user_id']==user
        assert [c['company_id'] for c in r.json()['data']['companies']]==companies
    for path in ('totals?business_month=2026-09','invoices/F002','bank-transactions?business_month=2026-09','purpose-check?business_month=2026-09','rules?business_month=2026-09&topic=purpose'):
        r=client.get('/api/v1/companies/C002/'+path,headers=headers('U002'))
        assert r.status_code==403
        validate('ErrorEnvelope',r.json())
        assert not any(x in r.text for x in ('12667.24','F002','amount','乙企业'))
    r=client.get('/api/v1/invoices/search?company_id=C002',headers=headers('U002'))
    assert r.status_code==403
    r=client.get('/api/v1/invoices/search?limit=100',headers=headers('U002'))
    assert len(r.json()['data']['items'])==20 and all(x['company_id']=='C001' for x in r.json()['data']['items'])
    assert client.get('/api/v1/me',headers={'X-User-ID':'U001'}).status_code==401


def test_TC007_empty_forbidden_storage_separate(client,pg):
    r=client.get('/api/v1/companies/C001/totals?business_month=2026-07',headers=headers())
    assert r.status_code==200 and r.json()['data']['invoice_total']=={'amount':'0.00','record_count':0,'empty':True}
    assert client.get('/api/v1/companies/C002/totals?business_month=2026-09',headers=headers('U002')).status_code==403
    service=pg[2]
    class FailedRead:
        def __enter__(self):raise OperationalError('fixture',{},Exception('TC007 synthetic connection failure'))
        def __exit__(self,*args):return False
    original=service.read_transaction;service.read_transaction=lambda:FailedRead()
    try:
        r=client.get('/api/v1/companies/C001/totals?business_month=2026-09',headers=headers())
        assert r.status_code==503 and r.json()['error']['code']=='STORAGE_UNAVAILABLE'
        assert '0.00' not in r.text and '9622' not in r.text
    finally:service.read_transaction=original


@pytest.mark.parametrize('month',['0000-09','2026-00','2026-13'])
def test_TC006_invalid_month_HTTP(client,month):
    r=client.get('/api/v1/companies/C001/totals',params={'business_month':month},headers=headers())
    assert r.status_code==422
    validate('ErrorEnvelope',r.json())


def test_TC011_HTTP_unsupported(client):
    r=client.get('/api/v1/companies/C001/purpose-check?business_month=2026-08',headers=headers())
    assert r.status_code==200
    data=r.json()['data'];validate('Check',data)
    assert data['check_status']=='unsupported' and data['count'] is None and data['missing'] is None


def test_TC013_search_keyset_and_filters(client):
    first=client.get('/api/v1/invoices/search?limit=3&company_id=C001',headers=headers()).json()['data']
    cursor=first['next_cursor'];assert cursor
    second=client.get('/api/v1/invoices/search',params=dict(limit=3,company_id='C001',cursor=cursor),headers=headers()).json()['data']
    assert {x['invoice_id'] for x in first['items']}.isdisjoint(x['invoice_id'] for x in second['items'])
    assert client.get('/api/v1/invoices/search',params=dict(company_id='C002',cursor=cursor),headers=headers()).status_code==422
    assert client.get('/api/v1/invoices/search',params=dict(company_id='C001',cursor=cursor),headers=headers('U002')).status_code==422
    for q in ('%','_',"' OR true --"):
        r=client.get('/api/v1/invoices/search',params=dict(q=q),headers=headers())
        assert r.status_code==200 and r.json()['data']['items']==[]
    bank=client.get('/api/v1/companies/C001/bank-transactions?business_month=2026-09&limit=2',headers=headers()).json()['data']
    second=client.get('/api/v1/companies/C001/bank-transactions',params=dict(business_month='2026-09',limit=2,cursor=bank['next_cursor']),headers=headers()).json()['data']
    assert {x['transaction_id'] for x in bank['items']}.isdisjoint(x['transaction_id'] for x in second['items'])
