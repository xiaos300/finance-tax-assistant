from pathlib import Path
from sqlalchemy import text
from alembic import command
from alembic.config import Config
from app.infrastructure.database.models import metadata
from app.infrastructure.database.seed import load_bundle
from app.infrastructure.database.targets import TargetError, instance_matches
import json


def verify_provenance(connection):
    # Existing matching names alone never authorize adopting/resetting an older database.
    from app.infrastructure.database.bootstrap import RECEIPT
    try:
        receipt=json.loads(RECEIPT.read_text(encoding='utf-8'))
        row=connection.execute(text("SELECT current_database(),oid::text,inet_server_addr()::text,inet_server_port() FROM pg_catalog.pg_database WHERE datname=current_database()")).one()
        roles=dict(connection.execute(text("SELECT rolname,oid::text FROM pg_catalog.pg_roles WHERE rolname IN ('finance_tax_app','finance_tax_migrator')")).all())
        if (receipt['database_oids'].get(row[0])!=row[1] or receipt['role_oids']!=roles
                or row[0] not in receipt.get('prepared_databases',receipt['database_oids'])
                or (receipt.get('source_kind')=='operator_precreated' and not receipt.get('approval_ref'))
                or not instance_matches(*receipt['identity'][4:6],*row[2:])):raise ValueError()
    except Exception:
        raise TargetError('Missing or mismatched project creation provenance; read-only review required before mutation') from None


def migrate(engine):
    cfg=Config(str(Path(__file__).resolve().parents[3]/'alembic.ini'))
    with engine.begin() as connection:
        verify_provenance(connection)
        cfg.attributes['connection']=connection
        command.upgrade(cfg,'head')


def grant_runtime(connection):
    verify_provenance(connection)
    # Fixed project SQL contains PostgreSQL format('%I'), not driver parameters.
    # Execute without a parameter collection, on the same guarded transaction.
    with connection.connection.driver_connection.cursor() as cursor:
        cursor.execute(Path(__file__).with_name('grant_runtime.sql').read_text(encoding='utf-8'))
    from app.infrastructure.database.permissions import assert_runtime_permissions
    assert_runtime_permissions(connection)


def inspect_prepared(connection):
    business,rules,manifest=load_bundle()
    revision=connection.scalar(text('SELECT version_num FROM harness.alembic_version'))
    marker=connection.execute(text('SELECT normalized_hash,schema_revision FROM harness.seed_meta')).one()
    if revision!='0001' or tuple(marker)!=(manifest['normalized_hash'],'0001'):
        raise ValueError('Schema revision or seed fingerprint differs')
    tables=set(connection.scalars(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='harness'")))
    if tables!={t.name for t in metadata.tables.values()}|{'alembic_version'}:raise ValueError('Schema table set differs')
    from app.infrastructure.database.seed import validate_existing
    validate_existing(connection,business,rules)
    from app.infrastructure.database.permissions import assert_runtime_permissions
    assert_runtime_permissions(connection)
    return {'schema_revision':revision,'seed_hash':marker[0]}


def reset_test(engine):
    # Factory guards run again for every new physical connection, before this transaction.
    with engine.begin() as connection:
        verify_provenance(connection)
        if connection.scalar(text('SELECT current_database()'))!='finance_tax_test':
            raise ValueError('Test reset target rejected')
        connection.execute(text('DROP SCHEMA harness CASCADE'))
        connection.execute(text('CREATE SCHEMA harness AUTHORIZATION finance_tax_migrator'))
        connection.execute(text('REVOKE ALL ON SCHEMA harness FROM PUBLIC'))
        connection.execute(text('GRANT USAGE ON SCHEMA harness TO finance_tax_app'))
