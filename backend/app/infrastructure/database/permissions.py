"""Check effective privileges, including grants inherited via PUBLIC."""
from sqlalchemy import text
from app.infrastructure.database.models import metadata

INSERT={'sessions','turns','messages','write_operations','tasks','preferences','evidence_events'}
UPDATE={'sessions','turns','messages','write_operations','tasks','preferences'}
DELETE={'tasks','preferences'}
COLUMN_UPDATE={'users':{'memory_revision'},'invoices':{'purpose','note','row_version','updated_at'}}


def assert_runtime_permissions(connection):
    base=connection.execute(text("""SELECT
        pg_catalog.has_database_privilege('finance_tax_app',current_database(),'CONNECT'),
        pg_catalog.has_database_privilege('finance_tax_app',current_database(),'CREATE'),
        pg_catalog.has_database_privilege('finance_tax_app',current_database(),'TEMP'),
        pg_catalog.has_schema_privilege('finance_tax_app','harness','USAGE'),
        pg_catalog.has_schema_privilege('finance_tax_app','harness','CREATE'),
        pg_catalog.has_schema_privilege('finance_tax_app','public','CREATE')""")).one()
    if tuple(base)!=(True,False,False,True,False,False):raise ValueError('Database or schema effective permissions differ')
    tables={t.name:t for t in metadata.tables.values()}
    for name in sorted(set(tables)|{'alembic_version'}):
        for privilege,allowed in [('SELECT',True),('INSERT',name in INSERT),('UPDATE',name in UPDATE),('DELETE',name in DELETE),('TRUNCATE',False),('REFERENCES',False),('TRIGGER',False),('MAINTAIN',False)]:
            effective=connection.scalar(text('SELECT pg_catalog.has_table_privilege(:role,:table,:privilege)'),dict(role='finance_tax_app',table='harness.'+name,privilege=privilege))
            if effective is not allowed:raise ValueError('Effective table permissions differ from runtime whitelist')
        if name in tables:
            for col in tables[name].columns:
                for privilege in ('SELECT','INSERT','UPDATE','REFERENCES'):
                    allowed=(privilege=='SELECT' or privilege=='INSERT' and name in INSERT or privilege=='UPDATE' and (name in UPDATE or col.name in COLUMN_UPDATE.get(name,set())))
                    effective=connection.scalar(text('SELECT pg_catalog.has_column_privilege(:role,:table,:column,:privilege)'),dict(role='finance_tax_app',table='harness.'+name,column=col.name,privilege=privilege))
                    if effective is not allowed:raise ValueError('Effective column permissions differ from runtime whitelist')
    seq=connection.scalar(text("SELECT pg_catalog.pg_get_serial_sequence('harness.evidence_events','event_id')"))
    for privilege,allowed in [('USAGE',True),('SELECT',True),('UPDATE',False)]:
        if connection.scalar(text('SELECT pg_catalog.has_sequence_privilege(:role,:sequence,:privilege)'),dict(role='finance_tax_app',sequence=seq,privilege=privilege)) is not allowed:
            raise ValueError('Effective evidence sequence permissions differ')
