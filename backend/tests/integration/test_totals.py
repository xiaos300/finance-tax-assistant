from datetime import date,datetime,timezone
import pytest
from sqlalchemy import text
from app.infrastructure.database.models import invoices


@pytest.mark.parametrize('company,month,expected',[
    ('C001','2026-08',['9046.35','5720.99','14850.75']),('C001','2026-09',['9622.06','7180.74','13000.50']),
    ('C002','2026-08',['13667.05','9341.10','18800.25']),('C002','2026-09',['12667.24','8087.24','13700.75'])])
def test_TC005_four_totals_and_purpose_invariance(pg,company,month,expected):
    app,maint,service=pg
    def amounts():
        r=service.totals('U001',company,month)
        return [r.invoice_total.amount,r.bank_expense.amount,r.bank_income.amount]
    assert amounts()==expected
    with app.begin() as c:c.execute(text('UPDATE harness.invoices SET purpose=:purpose WHERE company_id=:company'),{'purpose':'明确夹具用途','company':company})
    assert amounts()==expected


def test_TC006_boundaries(pg):
    _,maint,service=pg
    dates=[(date(2025,9,15),10),(date(2026,8,31),20),(date(2026,9,1),30),(date(2026,9,30),40),(date(2026,10,1),50)]
    with maint.begin() as c:
        for d,amount in dates:
            c.execute(invoices.insert().values(company_id='C001',invoice_id='DATE-'+d.isoformat(),invoice_date=d,seller='测试夹具',item_name='测试夹具',amount_cents=amount,purpose=None,note=None,row_version=1,updated_at=datetime.now(timezone.utc)))
    assert service.totals('U001','C001','2026-09').invoice_total.amount=='9622.76'
    rows=service.search('U001','C001','2026-09',q='DATE-',limit=100).items
    assert [r.invoice_id for r in rows]==['DATE-2026-09-01','DATE-2026-09-30']
    assert service.totals('U001','C001','2025-09').invoice_total.amount=='0.10'


def test_TC007_zero_records(pg):
    r=pg[2].totals('U001','C001','2026-07')
    assert all(getattr(r,k).amount=='0.00' and getattr(r,k).empty and getattr(r,k).record_count==0 for k in ('invoice_total','bank_expense','bank_income'))
