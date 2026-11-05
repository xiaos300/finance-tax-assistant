"""Explicit preparation of reviewed, operator-precreated project databases.

No database/role creation, password changes, ownership transfer or data overwrite.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import unicodedata

import psycopg
from psycopg import sql

from app.infrastructure.database import bootstrap
from app.infrastructure.database.targets import TargetError, instance_matches, parse_target, test_settings
from app.infrastructure.database.seed import load_bundle


def validate_approval(reference):
    if not isinstance(reference,str) or not reference.startswith('Documentation.md#') or len(reference)>500:
        raise TargetError('An explicit local approval reference is required for precreated objects')
    fragment=reference.split('#',1)[1]
    text=(bootstrap.ROOT/'Documentation.md').read_text(encoding='utf-8')
    titles=re.findall(r'^##\s+(.+)$',text,re.M)
    anchors=[''.join(c for c in title.lower() if c in '_- ' or unicodedata.category(c)[0] in 'LNM').replace(' ','-') for title in titles]
    if not fragment or fragment not in anchors:
        raise TargetError('Local approval reference does not identify a recorded decision')


def validate_existing_report(report,database):
    dbs={r[0]:r for r in report['existing_databases']}
    roles={r[0]:r for r in report['existing_roles']}
    expected={'finance_tax_app','finance_tax_migrator'}
    if (database not in ('finance_tax_dev','finance_tax_test') or set(dbs)!={'finance_tax_dev','finance_tax_test'}
            or any(tuple(r[1:3])!=('finance_tax_migrator','UTF8') for r in dbs.values())
            or set(roles)!=expected or report['memberships']
            or any(tuple(r[1:])!=(False,False,False,True,False,False) for r in roles.values())):
        raise TargetError('Existing database ownership/encoding or role attributes differ; no changes authorized')


def require_test_acceptance(path):
    try:
        evidence=json.loads(Path(path).read_text(encoding='utf-8'))
        if (evidence['stage']!='D1' or evidence['test_target']!='finance_tax_test'
                or evidence['d1_required_gate']!='passed'
                or evidence['test_counts']['blocked']!=0 or evidence['test_counts']['failed']!=0
                or evidence['test_counts']['passed']<=0
                or evidence['seed_hash']!=load_bundle()[2]['normalized_hash']):raise ValueError()
    except Exception:
        raise TargetError('Passed real serial D1 test acceptance is required before development preparation') from None


def verify_preparation_login(url,target,report):
    with psycopg.connect(host=target.host,hostaddr=target.host,port=target.port,dbname=target.database,
            user=target.role,password=url.password,connect_timeout=5,
            options='-c default_transaction_read_only=on -c statement_timeout=10000') as c:
        row=c.execute("SELECT current_database(),session_user,current_user,inet_server_addr()::text,inet_server_port(),oid::text FROM pg_database WHERE datname=current_database()").fetchone()
        role_oid=c.execute('SELECT oid::text FROM pg_roles WHERE rolname=current_user').fetchone()[0]
        if (row[:3]!=(target.database,target.role,target.role)
                or not instance_matches(row[3],row[4],target.host,target.port)
                or row[5]!=report['database_oids'][target.database] or role_oid!=report['role_oids'][target.role]):
            raise TargetError('Preparation login identity differs from inspected objects')
        c.rollback()


def prepare_existing(values,*,testing,approval_ref,acceptance=None):
    validate_approval(approval_ref)
    if values.get('app_env')!=('test' if testing else 'development') or values.get('pytest_xdist_worker'):
        raise TargetError('Explicit serial target environment is required')
    if testing:
        test_settings(values)
    else:
        require_test_acceptance(acceptance)
    report=bootstrap.inspect_admin(values)
    database='finance_tax_test' if testing else 'finance_tax_dev'
    validate_existing_report(report,database)
    app,target=parse_target(values.get('test_database_url' if testing else 'database_url',''),maintenance=False,testing=testing)
    maint,maint_target=parse_target(values.get('test_migration_database_url' if testing else 'migration_database_url',''),maintenance=True,testing=testing)
    if (not app.password or not maint.password or app.password==maint.password
            or not instance_matches(target.host,target.port,maint_target.host,maint_target.port)
            or not instance_matches(*report['identity'][4:6],target.host,target.port)):
        raise TargetError('Independent role credentials on the inspected instance are required')
    old=None
    if bootstrap.RECEIPT.exists():
        old=json.loads(bootstrap.RECEIPT.read_text(encoding='utf-8'))
        if (old.get('source_kind')!='operator_precreated' or old.get('approval_ref')!=approval_ref
                or old.get('system_identifier')!=report['system_identifier']
                or old.get('database_oids')!=report['database_oids'] or old.get('role_oids')!=report['role_oids']):
            raise TargetError('Existing preparation receipt differs; stop for review')
    if not testing and (not old or 'finance_tax_test' not in old.get('prepared_databases',[])):
        raise TargetError('Reviewed test database preparation must precede development')
    verify_preparation_login(app,target,report)
    verify_preparation_login(maint,maint_target,report)
    with bootstrap.admin_connect(values,database) as c:
        with c.transaction():
            # All validation below precedes the first object/ACL mutation.
            identity=c.execute('SELECT current_database(),session_user,current_user').fetchone()
            oid=c.execute('SELECT oid::text FROM pg_database WHERE datname=current_database()').fetchone()[0]
            role_oids=dict(c.execute("SELECT rolname,oid::text FROM pg_roles WHERE rolname IN ('finance_tax_app','finance_tax_migrator')").fetchall())
            if identity!=(database,'postgres','postgres') or oid!=report['database_oids'][database] or role_oids!=report['role_oids']:
                raise TargetError('Authenticated project object identities changed before preparation')
            schema=c.execute("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='harness'").fetchone()
            if schema and schema[0]!='finance_tax_migrator':raise TargetError('Existing harness schema owner differs')
            objects=c.execute("""SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname IN ('public','harness') AND c.relkind IN ('r','p','v','m','f','S','c')""").fetchone()[0]
            functions=c.execute("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('public','harness')").fetchone()[0]
            types=c.execute("SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname IN ('public','harness')").fetchone()[0]
            extra=c.execute("SELECT count(*) FROM pg_namespace WHERE nspname NOT IN ('public','harness','information_schema') AND nspname NOT LIKE 'pg_%'").fetchone()[0]
            if objects or functions or types or extra:raise TargetError('Precreated target is not empty; no adoption or overwrite attempted')
            if not schema:c.execute('CREATE SCHEMA harness AUTHORIZATION finance_tax_migrator')
            c.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC,finance_tax_app').format(sql.Identifier(database)))
            c.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO finance_tax_app').format(sql.Identifier(database)))
            for role in ('finance_tax_app','finance_tax_migrator'):
                c.execute(sql.SQL('ALTER ROLE {} IN DATABASE {} SET search_path TO harness,pg_catalog').format(sql.Identifier(role),sql.Identifier(database)))
            c.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
            c.execute('REVOKE ALL ON SCHEMA public FROM finance_tax_app')
            c.execute('REVOKE ALL ON SCHEMA harness FROM PUBLIC,finance_tax_app')
            c.execute('GRANT USAGE ON SCHEMA harness TO finance_tax_app')
            c.execute('ALTER DEFAULT PRIVILEGES FOR ROLE finance_tax_migrator IN SCHEMA harness REVOKE ALL ON TABLES FROM finance_tax_app')
            c.execute('ALTER DEFAULT PRIVILEGES FOR ROLE finance_tax_migrator IN SCHEMA harness REVOKE ALL ON SEQUENCES FROM finance_tax_app')
    prepared=set(old.get('prepared_databases',[])) if old else set()
    prepared.add(database)
    receipt={**report,'source_kind':'operator_precreated','approval_ref':approval_ref,
             'prepared_databases':sorted(prepared),'recorded_at':datetime.now(timezone.utc).isoformat()}
    bootstrap.RECEIPT.parent.mkdir(parents=True,exist_ok=True)
    tmp=bootstrap.RECEIPT.with_suffix('.tmp')
    tmp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(bootstrap.RECEIPT)
    return {'database':database,'source_kind':'operator_precreated','result':'schema_and_base_permissions_prepared'}
