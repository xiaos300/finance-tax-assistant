"""TC052 guards, shared configuration isolation subitems TC051/061. No network."""
import pytest
from app.infrastructure.database.targets import parse_target,test_settings as guarded_settings,verify_authenticated,Target,TargetError
from app.infrastructure.database.engine import connection_factory
from app.core.config import DatabaseSettings
from sqlalchemy.engine import make_url

APP=make_url('postgresql+psycopg://finance_tax_app@127.0.0.1/finance_tax_test').set(password='D1_SYNTHETIC_PASSWORD').render_as_string(hide_password=False)
MAINT=APP.replace('finance_tax_app','finance_tax_migrator')


def values():return dict(app_env='test',test_database_url=APP,test_migration_database_url=MAINT)


@pytest.mark.parametrize('db',['finance_tax_dev','tax_db','harness_test_d1','finance_tax_test_backup','other_test','','finance_tax_test_gw0','%66inance_tax_test'])
def test_TC052_wrong_database_rejected_before_engine(db,monkeypatch):
    monkeypatch.setattr('app.infrastructure.database.engine.create_engine',lambda *a,**k:pytest.fail('engine created for rejected target'))
    raw=APP.rsplit('/',1)[0]+'/'+db
    with pytest.raises((TargetError,ValueError)):
        connection_factory(DatabaseSettings(database_url=raw),testing=True)


@pytest.mark.parametrize('suffix',['?service=local','?hostaddr=127.0.0.1','?host=localhost','?dbname=tax_db','?options=-csearch_path=public','?port=5433','?sslmode=disable'])
def test_TC052_query_options_rejected(suffix):
    with pytest.raises(TargetError):parse_target(APP+suffix,maintenance=False,testing=True)


@pytest.mark.parametrize('role',['postgres','finance_tax_migrator','fixture','%66inance_tax_app'])
def test_TC052_wrong_role(role):
    raw=APP.replace('finance_tax_app',role)
    # SQLAlchemy decodes URL-encoded usernames, which cannot confer a different role.
    if role=='%66inance_tax_app':assert parse_target(raw,maintenance=False,testing=True)[1].role=='finance_tax_app'
    else:
        with pytest.raises(TargetError):parse_target(raw,maintenance=False,testing=True)


@pytest.mark.parametrize('host',['localhost','127.0.0.1'])
def test_TC052_loopback_default_port_canonical(host):
    _,target=parse_target(APP.replace('127.0.0.1',host),maintenance=False,testing=True)
    assert target.host=='127.0.0.1' and target.port==5432


@pytest.mark.parametrize('host',['127.0.0.1,localhost','127.1','%31%32%37.0.0.1','db','example.com','127.0.0.1:5433'])
def test_TC052_ambiguous_instance(host):
    with pytest.raises(TargetError):parse_target(APP.replace('127.0.0.1',host),maintenance=False,testing=True)


@pytest.mark.parametrize('key',['test_database_url','test_migration_database_url'])
def test_TC061_explicit_connections_no_fallback(key):
    v=values();v.pop(key);v['database_url']=APP
    with pytest.raises(TargetError):guarded_settings(v)


@pytest.mark.parametrize('change',[dict(app_env='development'),dict(app_env='demo'),dict(pytest_xdist_worker='gw0'),dict(test_migration_database_url=MAINT.replace('127.0.0.1','[::1]')),dict(database_url=APP.replace('127.0.0.1','localhost:5432'))])
def test_TC052_environment_or_instance_mismatch(change):
    v=values();v.update(change)
    with pytest.raises(TargetError):guarded_settings(v)


def test_TC052_safe_pair_and_no_model_dependency():
    v=values();v['model_mode']='invalid';a,m=guarded_settings(v)
    assert a.database_url and m.database_url


@pytest.mark.parametrize('index,value',[(None,None),(0,'tax_db'),(1,'postgres'),(2,'postgres'),(3,170000),(4,'127.0.0.2'),(5,5433),*[(i,True) for i in range(6,12)],(12,'postgres'),(13,'SQL_ASCII'),(14,'other_owner')])
def test_TC052_authenticated_mismatch_stops_before_writes(index,value):
    row=['finance_tax_test','finance_tax_app','finance_tax_app',180006,'127.0.0.1',5432,*([False]*6),'finance_tax_migrator','UTF8','finance_tax_migrator']
    if index is not None:row[index]=value
    class Cursor:
        def execute(self,sql):assert sql.lstrip().startswith('SELECT')
        def fetchone(self):return tuple(row)
    if index is None:verify_authenticated(Cursor(),Target('127.0.0.1',5432,'finance_tax_test','finance_tax_app'))
    else:
        with pytest.raises(TargetError):verify_authenticated(Cursor(),Target('127.0.0.1',5432,'finance_tax_test','finance_tax_app'))


def test_TC061_no_secret_in_rejection():
    with pytest.raises(TargetError) as exc:parse_target(APP.replace('finance_tax_test','tax_db'),maintenance=False,testing=True)
    assert 'D1_SYNTHETIC_PASSWORD' not in str(exc.value)
