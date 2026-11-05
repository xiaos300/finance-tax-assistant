import sys
from pathlib import Path
from datetime import date
import pytest
from app.modules.ledger.policies import month_bounds,money,is_blank,requires_purpose
from app.core.contracts import ThresholdPolicy
from app.core.exceptions import BusinessError
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from prepare_seed import cents


@pytest.mark.parametrize('month',['0000-09','2026-00','2026-13','26-09','2026-9','2026-09-01'])
def test_TC006_invalid_month(month):
    with pytest.raises(BusinessError):month_bounds(month)


def test_TC006_year_boundary():
    assert month_bounds('2026-12')==(date(2026,12,1),date(2027,1,1))


@pytest.mark.parametrize('value',[None,'',' ','\t\n','\u3000\u00a0\u2003'])
def test_TC009_unicode_blank(value):assert is_blank(value)


def test_TC009_note_does_not_affect_blank():assert not is_blank('用途')


@pytest.mark.parametrize('value',[99999,100000,100001])
def test_TC011_threshold(value):
    assert requires_purpose(value,ThresholdPolicy(kind='amount_gte',threshold_cents=100000))==(value>=100000)


@pytest.mark.parametrize('value',['NaN','Infinity','-1','0.001','bad','92233720368547758.08'])
def test_TC001_seed_precision_rejection(value):
    with pytest.raises(ValueError):cents(value)


def test_TC001_integer_money():
    assert cents('999.99')==99999
    assert cents('1.230')==123
    assert money(9223372036854775807)=='92233720368547758.07'
