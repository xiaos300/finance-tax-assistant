"""Explicit admin entry point. Existing names cause a read-only conflict report."""
import json
from datetime import datetime,timezone
from pathlib import Path
from ipaddress import ip_address
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.infrastructure.database.targets import TargetError, parse_target, instance_matches

ROOT=Path(__file__).resolve().parents[4]
RECEIPT=ROOT/'var/bootstrap-receipt.json'


def admin_connect(values, database='postgres'):
    try:
        if database not in ('postgres','finance_tax_dev','finance_tax_test'):raise ValueError()
        u=make_url(values.get('admin_database_url',''))
        host='127.0.0.1' if u.host=='localhost' else u.host
        if (u.drivername!='postgresql+psycopg' or u.username!='postgres' or u.database!='postgres'
                or u.query or not ip_address(host).is_loopback or (u.port or 5432)!=5432):raise ValueError()
        host=ip_address(host).compressed
        return psycopg.connect(host=host,hostaddr=host,port=5432,dbname=database,user=u.username,password=u.password,
            connect_timeout=5,options='-c statement_timeout=15000 -c lock_timeout=5000',autocommit=True)
    except Exception:
        raise TargetError('Controlled local administrator connection unavailable or rejected.') from None


def inspect_admin(values):
    with admin_connect(values) as c:
        with c.transaction():
            c.execute('SET TRANSACTION READ ONLY')
            r=c.execute("SELECT current_database(),session_user,current_user,current_setting('server_version_num')::int,inet_server_addr()::text,inet_server_port(),rolsuper FROM pg_catalog.pg_roles WHERE rolname=current_user").fetchone()
            u=make_url(values['admin_database_url']);host='127.0.0.1' if u.host=='localhost' else u.host
            if (not r or r[:3]!=('postgres','postgres','postgres') or not 180000<=r[3]<190000
                    or not instance_matches(r[4],r[5],host,5432) or r[6] is not True):
                raise TargetError('Administrator instance or identity rejected')
            roles=c.execute("SELECT rolname,rolsuper,rolcreatedb,rolcreaterole,rolcanlogin,rolreplication,rolbypassrls FROM pg_catalog.pg_roles WHERE rolname IN ('finance_tax_app','finance_tax_migrator') ORDER BY rolname").fetchall()
            databases=c.execute("SELECT datname,pg_catalog.pg_get_userbyid(datdba),pg_catalog.pg_encoding_to_char(encoding),datacl::text FROM pg_catalog.pg_database WHERE datname IN ('finance_tax_test','finance_tax_dev') ORDER BY datname").fetchall()
            role_oids=dict(c.execute("SELECT rolname,oid::text FROM pg_catalog.pg_roles WHERE rolname IN ('finance_tax_app','finance_tax_migrator')").fetchall())
            memberships=c.execute("SELECT r.rolname FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON m.member=r.oid WHERE r.rolname IN ('finance_tax_app','finance_tax_migrator')").fetchall()
            system_id=c.execute('SELECT system_identifier::text FROM pg_catalog.pg_control_system()').fetchone()[0]
            database_oids=dict(c.execute("SELECT datname,oid::text FROM pg_catalog.pg_database WHERE datname IN ('finance_tax_test','finance_tax_dev')").fetchall())
    return dict(identity=list(r),system_identifier=system_id,existing_roles=roles,existing_databases=databases,role_oids=role_oids,database_oids=database_oids,memberships=memberships)


def bootstrap(values, *, development=False, acceptance=None):
    if values.get('app_env')!=('development' if development else 'test') or values.get('pytest_xdist_worker'):
        raise TargetError('Bootstrap requires the explicit serial target environment')
    report=inspect_admin(values)
    db='finance_tax_dev' if development else 'finance_tax_test'
    conflict=any(r[0]==db for r in report['existing_databases']) or (report['existing_roles'] and not development)
    if not development and (report['existing_databases'] or RECEIPT.exists()):conflict=True
    if conflict:
        # Explicit report and stop. Never infer permission to adopt matching objects.
        print(json.dumps(report,ensure_ascii=False))
        raise TargetError('Existing project names require review; no object changes executed')
    if development:
        # Reuse only roles demonstrably created by this project's test bootstrap, not preexisting names.
        try:
            receipt=json.loads(RECEIPT.read_text(encoding='utf-8'))
            evidence=json.loads(Path(acceptance).read_text(encoding='utf-8'))
            from app.infrastructure.database.seed import load_bundle
            if (receipt['system_identifier']!=report['system_identifier'] or receipt['role_oids']!=report['role_oids']
                    or not instance_matches(*receipt['identity'][4:6],*report['identity'][4:6]) or report['memberships']
                    or len(report['existing_roles'])!=2
                    or any(tuple(r[1:])!=(False,False,False,True,False,False) for r in report['existing_roles'])
                    or not any(tuple(r[:3])==('finance_tax_test','finance_tax_migrator','UTF8') for r in report['existing_databases'])
                    or evidence.get('stage')!='D1'
                    or evidence.get('test_target')!='finance_tax_test' or evidence.get('d1_required_gate')!='passed'
                    or evidence.get('test_counts',{}).get('blocked')!=0 or evidence.get('test_counts',{}).get('failed')!=0
                    or evidence.get('seed_hash')!=load_bundle()[2]['normalized_hash']):raise ValueError()
        except Exception:
            print(json.dumps(report,ensure_ascii=False))
            raise TargetError('Development creation requires matching bootstrap provenance and passed real D1 acceptance') from None
    app,app_target=parse_target(values.get('database_url' if development else 'test_database_url',''),maintenance=False,testing=not development)
    maint,maint_target=parse_target(values.get('migration_database_url' if development else 'test_migration_database_url',''),maintenance=True,testing=not development)
    if not app.password or not maint.password or app_target.host!=maint_target.host:
        raise TargetError('Provide independent project passwords in controlled test connections')
    if app.password==maint.password:raise TargetError('Application and maintenance passwords must be independent')
    if development:
        test_app,test_target=parse_target(values.get('test_database_url',''),maintenance=False,testing=True)
        test_maint,test_maint_target=parse_target(values.get('test_migration_database_url',''),maintenance=True,testing=True)
        if test_target.host!=app_target.host or test_maint_target.host!=app_target.host or (app.password,maint.password)!=(test_app.password,test_maint.password):
            raise TargetError('Development credentials must match the project roles accepted on the test instance')
    admin=make_url(values['admin_database_url']);host='127.0.0.1' if admin.host=='localhost' else admin.host
    if not instance_matches(host,5432,app_target.host,app_target.port):raise TargetError('Admin and test instances differ')
    with admin_connect(values) as c:
        if not development:
            with c.transaction():
                for role,password in [('finance_tax_migrator',maint.password),('finance_tax_app',app.password)]:
                    c.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}').format(sql.Identifier(role),sql.Literal(password)))
        c.execute(sql.SQL("CREATE DATABASE {} OWNER finance_tax_migrator ENCODING 'UTF8' TEMPLATE template0").format(sql.Identifier(db)))
    with admin_connect(values,db) as c:
        with c.transaction():
            r=c.execute('SELECT current_database(),session_user,current_user').fetchone()
            if r!=(db,'postgres','postgres'):raise TargetError('Bootstrap target rejected')
            c.execute('CREATE SCHEMA harness AUTHORIZATION finance_tax_migrator')
            c.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC,finance_tax_app').format(sql.Identifier(db)))
            c.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO finance_tax_app').format(sql.Identifier(db)))
            for role in ('finance_tax_migrator','finance_tax_app'):
                c.execute(sql.SQL('ALTER ROLE {} IN DATABASE {} SET search_path TO harness,pg_catalog').format(sql.Identifier(role),sql.Identifier(db)))
            c.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
            c.execute('REVOKE ALL ON SCHEMA public FROM finance_tax_app')
            c.execute('REVOKE ALL ON SCHEMA harness FROM PUBLIC,finance_tax_app')
            c.execute('GRANT USAGE ON SCHEMA harness TO finance_tax_app')
            c.execute('ALTER DEFAULT PRIVILEGES FOR ROLE finance_tax_migrator IN SCHEMA harness REVOKE ALL ON TABLES FROM finance_tax_app')
            c.execute('ALTER DEFAULT PRIVILEGES FOR ROLE finance_tax_migrator IN SCHEMA harness REVOKE ALL ON SEQUENCES FROM finance_tax_app')
    if not development:
        receipt=inspect_admin(values)
        receipt['created_at']=datetime.now(timezone.utc).isoformat()
        RECEIPT.parent.mkdir(parents=True,exist_ok=True)
        with RECEIPT.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    else:
        receipt=inspect_admin(values)
        receipt['created_at']=datetime.now(timezone.utc).isoformat()
        RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'created_database':db,'roles':['finance_tax_migrator','finance_tax_app'],'schema':'harness'}
