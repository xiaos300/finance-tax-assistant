from datetime import datetime,timezone
from uuid import uuid4,uuid5,UUID
from pathlib import Path
import hashlib,json,subprocess,sys
import pytest
from sqlalchemy import text
from app.infrastructure.database import models as m
from app.infrastructure.database.seed import seed,load_bundle
from app.infrastructure.database.maintenance import reset_test,migrate


def test_TC002_committed_fixture_survives_process_restart_and_same_hash_seed(pg,record_property):
    app,maint,service=pg
    now=datetime.now(timezone.utc);session_id,turn_id,message_id,task_id=[str(uuid4()) for _ in range(4)]
    operation_id=str(uuid5(UUID(turn_id),json.dumps(['C001','F002'],ensure_ascii=False,separators=(',',':'))))
    purpose='客户方案资料打印'
    with maint.begin() as c:
        c.execute(m.sessions.insert().values(session_id=session_id,user_id='U001',default_company_id='C001',created_at=now,updated_at=now))
        result=dict(turn_id=turn_id,status='completed',outcome='answered',answer='TC002 直接构造合法夹具，非模型执行',session_state=dict(default_company_id='C001',row_version=1),scope=None,facts=[],writes=[],rule_refs=[],remaining=None,error=None,evidence_url=f'/api/v1/sessions/{session_id}/turns/{turn_id}/evidence')
        c.execute(m.turns.insert().values(turn_id=turn_id,session_id=session_id,request_hash='fixture',status='completed',session_version=1,memory_revision=1,result_json=result,started_at=now,finished_at=now))
        c.execute(m.messages.insert().values(message_id=message_id,turn_id=turn_id,role='user',content='请将甲企业 F002 用途补为客户方案资料打印，并持续补齐九月用途。',created_at=now))
        c.execute(m.invoices.update().where(m.invoices.c.company_id=='C001',m.invoices.c.invoice_id=='F002').values(purpose=purpose,row_version=2,updated_at=now))
        request_hash=hashlib.sha256(json.dumps(dict(company_id='C001',invoice_id='F002',changes={'purpose':purpose}),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        c.execute(m.write_operations.insert().values(operation_id=operation_id,turn_id=turn_id,user_id='U001',company_id='C001',invoice_id='F002',request_hash=request_hash,expected_row_version=1,authorization_json={'message_id':message_id,'action_evidence':{'quote':'请将','occurrence':0},'purpose_evidence':{'quote':purpose,'occurrence':0},'object_source':'explicit','fixture':True},changes_json={'purpose':purpose},before_json={'purpose':None},after_json={'purpose':purpose},state='verified',created_at=now,committed_at=now,verified_at=now))
        progress=dict(completed_operation_ids=[operation_id],pending_operation_ids=[],remaining=None,missing_fields=[],snapshot_stale=True,as_of=now.isoformat().replace('+00:00','Z'))
        c.execute(m.tasks.insert().values(task_id=task_id,user_id='U001',company_id='C001',goal='持续补齐九月用途',business_month='2026-09',status='active',progress_json=progress,source_turn_id=turn_id,last_change_origin_json={'kind':'chat','request_id':'TC002-fixture','turn_id':turn_id},created_at=now,updated_at=now))
        c.execute(m.users.update().where(m.users.c.user_id=='U001').values(memory_revision=1))
    app.dispose();maint.dispose()
    # Separate process represents a stopped/restarted application DB connection lifecycle.
    script="from app.infrastructure.database.targets import test_settings;from app.infrastructure.database.engine import connection_factory;from sqlalchemy import text;e,_=connection_factory(test_settings()[0],testing=True);c=e.connect();assert c.scalar(text(\"SELECT purpose FROM harness.invoices WHERE company_id='C001' AND invoice_id='F002'\"))=='客户方案资料打印';assert c.scalar(text('SELECT count(*) FROM harness.tasks'))==1;c.close();e.dispose();print('committed fixture preserved')"
    process=subprocess.run([sys.executable,'-c',script],capture_output=True,encoding='utf-8')
    assert process.returncode==0, 'Restarted read-only process failed'
    record_property('restart_process_exit_code',process.returncode)
    with maint.begin() as c:assert seed(c)=='verified_existing'
    assert service.invoice('U001','C001','F002').purpose==purpose
    with app.connect() as c:assert c.scalar(text('SELECT count(*) FROM harness.tasks'))==1


def test_TC002_different_hash_and_partial_database_refused(pg,tmp_path):
    _,maint,service=pg
    b,r,manifest=load_bundle()
    b['invoices'][0]['purpose']='different input'
    manifest['normalized_hash']=hashlib.sha256(json.dumps([b,r],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for name,content in [('business',b),('rules',r),('manifest',manifest)]:
        (tmp_path/f'{name}.json').write_text(json.dumps(content,ensure_ascii=False),encoding='utf-8')
    before=service.invoice('U001','C001','F002').model_dump()
    with pytest.raises(ValueError):
        with maint.begin() as c:seed(c,tmp_path)
    assert service.invoice('U001','C001','F002').model_dump()==before
    reset_test(maint);migrate(maint)
    with maint.begin() as c:c.execute(m.companies.insert().values(company_id='C001',name='partial fixture',short_name='partial'))
    with pytest.raises(ValueError):
        with maint.begin() as c:seed(c)
    with maint.connect() as c:
        assert c.scalar(text('SELECT count(*) FROM harness.companies'))==1
        assert c.scalar(text('SELECT count(*) FROM harness.seed_meta'))==0


def test_TC002_guarded_rebuild(pg):
    _,maint,_=pg
    reset_test(maint);migrate(maint)
    with maint.begin() as c:assert seed(c)=='loaded'
    with maint.connect() as c:assert c.scalar(text('SELECT count(*) FROM harness.invoices'))==40
