from datetime import datetime,timezone
import pytest
from sqlalchemy import inspect,select,text
from sqlalchemy.exc import IntegrityError
from app.infrastructure.database import models as m


def test_TC001_schema_counts_types_and_ownership(pg):
    app,maint,_=pg
    expected={'companies':2,'users':2,'user_company_permissions':4,'invoices':40,'bank_transactions':48,'rules':5}
    with app.connect() as c:
        assert c.scalar(text("SELECT current_setting('TimeZone')"))=='UTC'
        assert c.scalar(text("SELECT current_setting('search_path')"))=='harness,pg_catalog'
        for name,count in expected.items():assert c.scalar(text(f'SELECT count(*) FROM harness.{name}'))==count
        for cid in ('C001','C002'):
            for month in ('2026-08','2026-09'):
                assert c.scalar(text("SELECT count(*) FROM harness.invoices WHERE company_id=:cid AND to_char(invoice_date,'YYYY-MM')=:month"),dict(cid=cid,month=month))==10
                for direction,count in [('expense',8),('income',4)]:
                    assert c.scalar(text("SELECT count(*) FROM harness.bank_transactions WHERE company_id=:cid AND to_char(transaction_date,'YYYY-MM')=:month AND direction=:direction"),dict(cid=cid,month=month,direction=direction))==count
        assert c.scalar(text("SELECT count(*) FROM pg_catalog.pg_tables WHERE schemaname='harness' AND tableowner='finance_tax_migrator'"))==16
    inspector=inspect(maint)
    assert str(next(c['type'] for c in inspector.get_columns('invoices',schema='harness') if c['name']=='amount_cents'))=='BIGINT'
    assert str(next(c['type'] for c in inspector.get_columns('turns',schema='harness') if c['name']=='scope_company_ids'))=='JSONB'
    for table in m.metadata.tables.values():assert set(c.name for c in table.columns)=={c['name'] for c in inspector.get_columns(table.name,schema='harness')}


def insert_conversation(c):
    now=datetime.now(timezone.utc)
    c.execute(m.sessions.insert().values(session_id='fixture-session',user_id='U001',default_company_id='C001',row_version=1,created_at=now,updated_at=now))
    c.execute(m.turns.insert().values(turn_id='fixture-turn',session_id='fixture-session',request_hash='fixture',status='running',session_version=1,memory_revision=0,started_at=now))
    return now


def test_TC052_unique_foreign_keys_and_shapes(pg,record_property):
    maint=pg[1]
    with maint.begin() as c:
        now=insert_conversation(c)
        cases=[
            m.turns.insert().values(turn_id='second-running',session_id='fixture-session',request_hash='fixture',status='running',session_version=1,memory_revision=0,started_at=now),
            m.sessions.insert().values(session_id='unknown-permission',user_id='U001',default_company_id='MISSING',row_version=1,created_at=now,updated_at=now),
            m.turns.update().where(m.turns.c.turn_id=='fixture-turn').values(scope_company_ids={}),
            m.invoices.update().values(row_version=0),
            m.permissions.update().values(can_read=False,can_write=True),
            m.turns.update().values(status='completed'),
        ]
        for statement in cases:
            with pytest.raises(IntegrityError) as exc:
                with c.begin_nested():c.execute(statement)
            assert exc.value.orig.sqlstate in ('23505','23503','23514')
            record_property('constraint_sqlstate',exc.value.orig.sqlstate)
        base=dict(user_id='U001',company_id='C001',goal='明确 fixture 任务',business_month='2026-09',status='verify_pending',progress_json=dict(completed_operation_ids=[],pending_operation_ids=[],remaining=None,missing_fields=[],snapshot_stale=True,as_of=None),source_turn_id='fixture-turn',last_change_origin_json={'kind':'chat','request_id':'fixture','turn_id':'fixture-turn'},row_version=1,created_at=now,updated_at=now)
        c.execute(m.tasks.insert().values(task_id='task-one',**base))
        with pytest.raises(IntegrityError):
            with c.begin_nested():c.execute(m.tasks.insert().values(task_id='task-two',**base))
        pref=dict(user_id='U001',company_id='C001',preference_key='default_company',content='C001',source_turn_id='fixture-turn',last_change_origin_json={'kind':'chat','request_id':'fixture','turn_id':'fixture-turn'},row_version=1,created_at=now,updated_at=now)
        c.execute(m.preferences.insert().values(preference_id='pref-one',**pref))
        pref.update(company_id='C002',content='C002')
        with pytest.raises(IntegrityError):
            with c.begin_nested():c.execute(m.preferences.insert().values(preference_id='pref-two',**pref))
