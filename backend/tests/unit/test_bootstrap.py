import pytest
from app.infrastructure.database import bootstrap as b
from app.infrastructure.database.targets import TargetError


def test_TC052_existing_names_stop_before_mutation(monkeypatch):
    monkeypatch.setattr(b,'inspect_admin',lambda v:dict(existing_databases=[('finance_tax_test','other_owner','UTF8',None)],existing_roles=[('finance_tax_app',)],memberships=[]))
    monkeypatch.setattr(b,'admin_connect',lambda *a,**k:pytest.fail('mutation attempted on existing names'))
    with pytest.raises(TargetError):b.bootstrap({'app_env':'test'})


def test_TC052_development_creation_requires_real_test_acceptance(monkeypatch,tmp_path):
    monkeypatch.setattr(b,'inspect_admin',lambda v:dict(existing_databases=[('finance_tax_test','finance_tax_migrator','UTF8',None)],existing_roles=[],memberships=[]))
    monkeypatch.setattr(b,'RECEIPT',tmp_path/'absent.json')
    monkeypatch.setattr(b,'admin_connect',lambda *a,**k:pytest.fail('development mutation before gate'))
    with pytest.raises(TargetError):b.bootstrap({'app_env':'development'},development=True,acceptance=tmp_path/'missing.json')


def test_TC052_admin_tax_target_rejected_without_connection(monkeypatch):
    monkeypatch.setattr(b.psycopg,'connect',lambda **kw:pytest.fail('admin connection attempted'))
    with pytest.raises(TargetError):b.admin_connect({'admin_database_url':'postgresql+psycopg://postgres@127.0.0.1/tax_db'})


@pytest.mark.parametrize('database',['tax_db','other_database','finance_tax_test_backup'])
def test_TC052_admin_internal_override_cannot_target_unapproved_database(monkeypatch,database):
    monkeypatch.setattr(b.psycopg,'connect',lambda **kw:pytest.fail('Unapproved database connection attempted'))
    with pytest.raises(TargetError):
        b.admin_connect({'admin_database_url':'postgresql+psycopg://postgres@127.0.0.1/postgres'},database)
