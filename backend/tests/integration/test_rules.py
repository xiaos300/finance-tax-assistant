from datetime import date,datetime,timezone
from sqlalchemy import text
from app.infrastructure.database.models import rules,rule_companies


def test_TC009_blank_and_note(pg):
    app,_,s=pg
    def ids():return [x.invoice_id for x in s.check('U001','C001','2026-09').missing]
    assert ids()==['F002','F003','F004','F006','F009']
    assert s.check('U001','C001','2026-09').rule_refs[0].version=='2.0'
    with app.begin() as c:
        c.execute(text("UPDATE harness.invoices SET purpose=:blank WHERE company_id='C001' AND invoice_id='F001'"),{'blank':'\u3000\u00a0\t'})
        c.execute(text("UPDATE harness.invoices SET note=:note WHERE company_id='C001' AND invoice_id='F002'"),{'note':'备注不是用途'})
    assert ids()==['F001','F002','F003','F004','F006','F009']


def test_TC011_september_only_and_company_threshold(pg):
    s=pg[2]
    r=s.check('U001','C001','2026-08')
    assert r.check_status=='unsupported' and r.missing is None and r.count is None and r.rule_refs==[]
    assert s.totals('U001','C001','2026-08').invoice_total.amount=='9046.35'
    r=s.check('U001','C002','2026-09')
    assert [x.invoice_id for x in r.missing]==['F002','F005','F006']
    assert r.rule_refs[0].rule_id=='R003'


def test_TC027_missing_conflict_midmonth(pg):
    _,maint,s=pg
    with maint.begin() as c:c.execute(text("UPDATE harness.rules SET status='disabled' WHERE rule_id='R002'"))
    assert s.check('U001','C001','2026-09').check_status=='insufficient_rules'
    assert s.check('U001','C001','2026-09').count is None
    with maint.begin() as c:
        c.execute(text("UPDATE harness.rules SET status='enabled' WHERE rule_id='R002' AND version='2.0'"))
        row=dict(rule_id='R002',version='test',name='测试冲突',topic='purpose',effective_from=date(2026,9,1),status='enabled',body='测试规则正文',policy_json={'kind':'all'},revision=1,source_ref='TC027 fixture',content_hash='fixture',updated_at=datetime.now(timezone.utc))
        c.execute(rules.insert().values(**row));c.execute(rule_companies.insert().values(rule_id='R002',version='test',company_id='C001'))
    assert s.check('U001','C001','2026-09').check_status=='rule_conflict'
    with maint.begin() as c:
        c.execute(text("UPDATE harness.rules SET status='disabled' WHERE rule_id='R002' AND version='2.0'"))
        c.execute(text("UPDATE harness.rules SET effective_from='2026-09-15' WHERE rule_id='R002' AND version='test'"))
    r=s.check('U001','C001','2026-09')
    assert r.check_status=='unsupported' and r.count is None and r.missing is None
    assert s.totals('U001','C001','2026-09').invoice_total.amount=='9622.06'
