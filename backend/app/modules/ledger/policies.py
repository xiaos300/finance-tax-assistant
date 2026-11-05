"""Pure deterministic rules; no I/O or precomputed business answers."""
from datetime import date
import re
from app.core.exceptions import BusinessError


def month_bounds(month):
    if not isinstance(month,str) or not re.fullmatch(r'(?!0000)[0-9]{4}-(0[1-9]|1[0-2])',month):
        raise BusinessError('INVALID_MONTH')
    y,m=map(int,month.split('-'))
    if y==9999 and m==12:return date(y,m,1),None
    return date(y,m,1),date(y+int(m==12),1 if m==12 else m+1,1)


def money(cents):
    if isinstance(cents,bool) or not isinstance(cents,int) or cents<0:raise ValueError('Expected nonnegative integer cents')
    return f'{cents//100}.{cents%100:02d}'


def is_blank(value):
    return value is None or value.strip()==''


def requires_purpose(amount_cents,policy):
    if policy.kind=='all':return True
    if policy.kind=='amount_gte':return amount_cents>=policy.threshold_cents
    raise ValueError('Unsupported purpose strategy')
