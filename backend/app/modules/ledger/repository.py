from sqlalchemy import select,func,or_,tuple_
from app.infrastructure.database import models as m


class LedgerRepository:
    def __init__(self,session):self.session=session

    def access(self,user_id):
        user=self.session.execute(select(m.users).where(m.users.c.user_id==user_id)).mappings().one_or_none()
        companies=self.session.execute(select(m.companies.c.company_id,m.companies.c.name,m.permissions.c.can_write)
            .join(m.permissions,m.permissions.c.company_id==m.companies.c.company_id)
            .where(m.permissions.c.user_id==user_id,m.permissions.c.can_read.is_(True)).order_by(m.companies.c.company_id)).mappings().all()
        return dict(user) if user is not None else None,[dict(c) for c in companies]

    def metric(self,table,company,start,end,direction=None):
        t=m.invoices if table=='invoice' else m.bank_transactions
        d=t.c.invoice_date if table=='invoice' else t.c.transaction_date
        q=select(func.sum(t.c.amount_cents),func.count()).where(t.c.company_id==company,d>=start)
        if end is not None:q=q.where(d<end)
        if direction:q=q.where(t.c.direction==direction)
        amount,count=self.session.execute(q).one()
        if amount is not None and amount!=int(amount):raise ValueError('Noninteger sum')
        return int(amount or 0),count

    def invoices(self,companies,*,company=None,start=None,end=None,q='',last=None,limit=None):
        t=m.invoices
        query=select(t,m.companies.c.name.label('company_name')).join(m.companies,m.companies.c.company_id==t.c.company_id).where(t.c.company_id.in_(companies))
        if company:query=query.where(t.c.company_id==company)
        if start:query=query.where(t.c.invoice_date>=start)
        if end:query=query.where(t.c.invoice_date<end)
        if q:
            escaped=q.replace('\\','\\\\').replace('%',r'\%').replace('_',r'\_')
            query=query.where(or_(*(c.ilike('%'+escaped+'%',escape='\\') for c in (t.c.invoice_id,t.c.seller,t.c.item_name))))
        if last:query=query.where(tuple_(t.c.company_id,t.c.invoice_id)>tuple(last))
        query=query.order_by(t.c.company_id,t.c.invoice_id)
        if limit:query=query.limit(limit)
        return [dict(r) for r in self.session.execute(query).mappings()]

    def invoice(self,company,invoice):
        r=self.session.execute(select(m.invoices,m.companies.c.name.label('company_name')).join(m.companies,m.companies.c.company_id==m.invoices.c.company_id)
            .where(m.invoices.c.company_id==company,m.invoices.c.invoice_id==invoice)).mappings().one_or_none()
        return dict(r) if r else None

    def banks(self,company,start,end,last,limit):
        t=m.bank_transactions
        query=select(t).where(t.c.company_id==company,t.c.transaction_date>=start)
        if end:query=query.where(t.c.transaction_date<end)
        if last:
            from datetime import date
            query=query.where(tuple_(t.c.transaction_date,t.c.transaction_id)>tuple([date.fromisoformat(last[0]),last[1]]))
        return [dict(r) for r in self.session.execute(query.order_by(t.c.transaction_date,t.c.transaction_id).limit(limit)).mappings()]
