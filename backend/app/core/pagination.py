import base64
import hashlib
import json
from app.core.exceptions import BusinessError


def fingerprint(filters):
    return hashlib.sha256(json.dumps(filters,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def encode(resource,filters,user_id,last):
    return base64.urlsafe_b64encode(json.dumps(dict(v=1,resource=resource,filters_hash=fingerprint(filters),user_id=user_id,last_keys=last),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).decode().rstrip('=')


def decode(cursor,resource,filters,user_id,*,bank=False):
    if cursor is None:return None
    try:
        if len(cursor)>2000:raise ValueError()
        d=json.loads(base64.b64decode(cursor+'='*(-len(cursor)%4),altchars=b'-_',validate=True))
        if set(d)!={'v','resource','filters_hash','user_id','last_keys'} or type(d['v']) is not int or d['v']!=1 or d['resource']!=resource or d['filters_hash']!=fingerprint(filters) or d['user_id']!=user_id:raise ValueError()
        last=d['last_keys']
        if not isinstance(last,list) or len(last)!=2 or not all(isinstance(x,str) and 1<=len(x)<=128 for x in last):raise ValueError()
        if bank:
            from datetime import date
            if date.fromisoformat(last[0]).isoformat()!=last[0]:raise ValueError()
        elif last[0] not in ('C001','C002'):raise ValueError()
        return last
    except Exception:raise BusinessError('VALIDATION_ERROR') from None
