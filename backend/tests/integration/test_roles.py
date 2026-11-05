import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from app.infrastructure.database.maintenance import grant_runtime

DENIED=[
    'CREATE TABLE harness.denied_table(id integer)',
    'CREATE SCHEMA denied_schema',
    'CREATE DATABASE denied_database',
    'CREATE ROLE denied_role',
    "UPDATE harness.invoices SET amount_cents=1 WHERE company_id='C001' AND invoice_id='F002'",
    "UPDATE harness.invoices SET invoice_date='2026-09-01' WHERE company_id='C001' AND invoice_id='F002'",
    "UPDATE harness.invoices SET invoice_id='changed' WHERE company_id='C001' AND invoice_id='F002'",
    'DELETE FROM harness.invoices WHERE false',
    "INSERT INTO harness.invoices(company_id,invoice_id) VALUES('C001','ILLEGAL')",
    'UPDATE harness.bank_transactions SET amount_cents=1 WHERE false',
    'UPDATE harness.user_company_permissions SET can_write=true WHERE false',
    "UPDATE harness.users SET name='changed' WHERE false",
    "UPDATE harness.rules SET body='changed' WHERE false",
    "UPDATE harness.seed_meta SET normalized_hash='changed' WHERE false",
    "UPDATE harness.alembic_version SET version_num='changed' WHERE false",
    'CREATE TEMP TABLE denied_temp(id integer)',
]


@pytest.mark.parametrize('statement',DENIED)
def test_TC052_native_permission_denials(pg,statement,record_property):
    app=pg[0]
    # CREATE DATABASE cannot run inside a transaction; AUTOCOMMIT proves permission SQLSTATE.
    with app.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
        with pytest.raises(DBAPIError) as exc:c.execute(text(statement))
        assert exc.value.orig.sqlstate=='42501'
        record_property('denied_sqlstate',exc.value.orig.sqlstate)


def test_TC052_grants_converge_after_table_and_column_overgrant(pg,record_property):
    app,maint,_=pg
    with maint.begin() as c:
        c.execute(text('GRANT UPDATE ON harness.invoices TO finance_tax_app'))
        c.execute(text('GRANT UPDATE(amount_cents) ON harness.invoices TO finance_tax_app'))
        c.execute(text('GRANT UPDATE ON harness.bank_transactions TO finance_tax_app'))
        c.execute(text('GRANT UPDATE(amount_cents) ON harness.bank_transactions TO finance_tax_app'))
    with maint.begin() as c:grant_runtime(c)
    for statement in (DENIED[4],DENIED[9]):
        with app.connect() as c:
            with pytest.raises(DBAPIError) as exc:c.execute(text(statement))
            assert exc.value.orig.sqlstate=='42501'
            record_property('regrant_sqlstate',exc.value.orig.sqlstate)


def test_TC052_allowed_columns_and_independent_readback(pg):
    app,_,_=pg
    with app.begin() as c:
        c.execute(text("UPDATE harness.users SET memory_revision=memory_revision+1 WHERE user_id='U001'"))
        c.execute(text("UPDATE harness.invoices SET purpose=:purpose,note=:note,row_version=row_version+1,updated_at=now() WHERE company_id='C001' AND invoice_id='F002'"),{'purpose':'受控测试夹具','note':'备注'})
    # New physical connection after committed transaction, not same Session cache.
    app.dispose()
    with app.connect() as c:
        assert c.execute(text("SELECT purpose,note,row_version FROM harness.invoices WHERE company_id='C001' AND invoice_id='F002'")).one()==('受控测试夹具','备注',2)
        assert c.scalar(text("SELECT memory_revision FROM harness.users WHERE user_id='U001'"))==1
