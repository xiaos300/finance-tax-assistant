import copy
import json
import pytest
from sqlalchemy.engine import URL
from app.infrastructure.database import preparation as p
from app.infrastructure.database.targets import TargetError


def report():
    return {'existing_databases':[['finance_tax_dev','finance_tax_migrator','UTF8',None],['finance_tax_test','finance_tax_migrator','UTF8',None]],
        'existing_roles':[[name,False,False,False,True,False,False] for name in ('finance_tax_app','finance_tax_migrator')],
        'memberships':[]}


def test_TC052_precreated_matching_owned_objects():
    for db in ('finance_tax_dev','finance_tax_test'):p.validate_existing_report(report(),db)


@pytest.mark.parametrize('change',['owner','encoding','superuser','no_login','membership','missing_database','missing_role','unknown_database'])
def test_TC052_precreated_mismatch_stops(change):
    r=report();db='finance_tax_test'
    if change=='owner':r['existing_databases'][0][1]='postgres'
    elif change=='encoding':r['existing_databases'][1][2]='SQL_ASCII'
    elif change=='superuser':r['existing_roles'][0][1]=True
    elif change=='no_login':r['existing_roles'][1][4]=False
    elif change=='membership':r['memberships']=[['finance_tax_app']]
    elif change=='missing_database':r['existing_databases'].pop()
    elif change=='missing_role':r['existing_roles'].pop()
    else:db='tax_db'
    with pytest.raises(TargetError):p.validate_existing_report(r,db)


def test_TC052_precreated_requires_explicit_recorded_reference(monkeypatch,tmp_path):
    monkeypatch.setattr(p.bootstrap,'ROOT',tmp_path)
    (tmp_path/'Documentation.md').write_text('## Approved D1\n',encoding='utf-8')
    p.validate_approval('Documentation.md#approved-d1')
    for ref in (None,'','Other.md#approved-d1','Documentation.md#missing'):
        with pytest.raises(TargetError):p.validate_approval(ref)


def test_TC052_precreated_no_implicit_adoption(monkeypatch):
    monkeypatch.setattr(p.bootstrap,'inspect_admin',lambda values:pytest.fail('Must reject missing approval before any connection'))
    with pytest.raises(TargetError):p.prepare_existing({'app_env':'test'},testing=True,approval_ref=None)


def test_TC052_precreated_same_role_password_stops_before_mutation(monkeypatch):
    monkeypatch.setattr(p,'validate_approval',lambda reference:None)
    monkeypatch.setattr(p,'test_settings',lambda values:None)
    r={**report(),'identity':['postgres','postgres','postgres',180006,'127.0.0.1/32',5432,True]}
    monkeypatch.setattr(p.bootstrap,'inspect_admin',lambda values:r)
    monkeypatch.setattr(p,'verify_preparation_login',lambda *args:pytest.fail('Must reject reused credentials before further login or mutation'))
    def url(user):
        return URL.create('postgresql+psycopg',username=user,password='TC052_SYNTHETIC_SHARED',host='127.0.0.1',database='finance_tax_test').render_as_string(hide_password=False)
    v={'app_env':'test','test_database_url':url('finance_tax_app'),'test_migration_database_url':url('finance_tax_migrator')}
    with pytest.raises(TargetError,match='Independent role credentials'):
        p.prepare_existing(v,testing=True,approval_ref='Documentation.md#synthetic')


@pytest.mark.parametrize('flag',['blocked','failed','empty','wrong_target','wrong_hash'])
def test_TC052_development_requires_actual_test_gate(monkeypatch,tmp_path,flag):
    monkeypatch.setattr(p,'load_bundle',lambda:(None,None,{'normalized_hash':'expected'}))
    evidence={'stage':'D1','test_target':'finance_tax_test','d1_required_gate':'passed','test_counts':{'passed':100,'blocked':0,'failed':0},'seed_hash':'expected'}
    if flag=='blocked':evidence['test_counts']['blocked']=1
    elif flag=='failed':evidence['test_counts']['failed']=1
    elif flag=='empty':evidence['test_counts']['passed']=0
    elif flag=='wrong_target':evidence['test_target']='finance_tax_dev'
    else:evidence['seed_hash']='different'
    f=tmp_path/'summary.json';f.write_text(json.dumps(evidence),encoding='utf-8')
    with pytest.raises(TargetError):p.require_test_acceptance(f)
