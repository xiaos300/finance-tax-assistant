from datetime import datetime,timezone
from app.core.contracts import (Principal,Invoice,InvoiceSearchItem,InvoicePage,BankTransaction,BankPage,
                               Totals,Metric,Check,MissingInvoice)
from app.core.exceptions import BusinessError
from app.core import pagination
from app.modules.ledger.policies import month_bounds,money,is_blank,requires_purpose
from app.modules.knowledge.policies import resolve


def utc_now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')


class LedgerService:
    def __init__(self,read_transaction):self.read_transaction=read_transaction

    @staticmethod
    def principal(tx,user_id,company=None):
        user,companies=tx.ledger.access(user_id)
        if user is None:raise BusinessError('UNAUTHENTICATED',401,'身份无效')
        p=Principal(user_id=user['user_id'],name=user['name'],companies=companies)
        if company and company not in [c.company_id for c in p.companies]:
            raise BusinessError('FORBIDDEN',403,'当前身份无权执行此操作')
        return p

    def me(self,user):
        with self.read_transaction() as tx:return self.principal(tx,user)

    def totals(self,user,company,month,metrics=None):
        start,end=month_bounds(month)
        selected=metrics.split(',') if metrics is not None else ['invoice_total','bank_expense','bank_income']
        if not selected or len(set(selected))!=len(selected) or set(selected)-{'invoice_total','bank_expense','bank_income'}:
            raise BusinessError('VALIDATION_ERROR')
        with self.read_transaction() as tx:
            self.principal(tx,user,company)
            resolution=resolve(tx.knowledge.candidates(company,'amount'),month,'amount')
            basis='resolved' if resolution.resolution_status=='resolved' else 'rule_conflict' if resolution.resolution_status=='conflict' else 'insufficient_rules'
            data={}
            for key in selected:
                amount,count=tx.ledger.metric('invoice' if key=='invoice_total' else 'bank',company,start,end,
                    None if key=='invoice_total' else 'expense' if key=='bank_expense' else 'income')
                data[key]=Metric(amount=money(amount),record_count=count,empty=count==0)
            return Totals(company_id=company,business_month=month,currency='CNY',basis_status=basis,rule_refs=resolution.rule_refs,**data)

    @staticmethod
    def item(row,detail=False):
        data={k:row[k] for k in ('company_id','company_name','invoice_id','seller','item_name','row_version')}
        data.update(invoice_date=row['invoice_date'].isoformat(),amount=money(row['amount_cents']))
        if detail:
            data.update(purpose=row['purpose'],note=row['note'],updated_at=row['updated_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z'))
        return (Invoice if detail else InvoiceSearchItem)(**data)

    def invoice(self,user,company,invoice):
        with self.read_transaction() as tx:
            self.principal(tx,user,company)
            row=tx.ledger.invoice(company,invoice)
            if row is None:raise BusinessError('RESOURCE_NOT_FOUND',404,'未找到记录')
            return self.item(row,True)

    def search(self,user,company=None,month=None,q='',cursor=None,limit=20):
        start,end=month_bounds(month) if month else (None,None)
        if not 1<=limit<=100 or len(q)>500:raise BusinessError('VALIDATION_ERROR')
        filters=dict(company_id=company,business_month=month,q=q)
        last=pagination.decode(cursor,'invoices',filters,user)
        with self.read_transaction() as tx:
            p=self.principal(tx,user,company)
            rows=tx.ledger.invoices([c.company_id for c in p.companies],company=company,start=start,end=end,q=q,last=last,limit=limit+1)
            more=len(rows)>limit;rows=rows[:limit]
            next_cursor=pagination.encode('invoices',filters,user,[rows[-1]['company_id'],rows[-1]['invoice_id']]) if more else None
            return InvoicePage(items=[self.item(r) for r in rows],next_cursor=next_cursor)

    def banks(self,user,company,month,cursor=None,limit=20):
        start,end=month_bounds(month)
        if not 1<=limit<=100:raise BusinessError('VALIDATION_ERROR')
        filters=dict(company_id=company,business_month=month)
        last=pagination.decode(cursor,'bank',filters,user,bank=True)
        with self.read_transaction() as tx:
            self.principal(tx,user,company)
            rows=tx.ledger.banks(company,start,end,last,limit+1)
            more=len(rows)>limit;rows=rows[:limit]
            next_cursor=pagination.encode('bank',filters,user,[rows[-1]['transaction_date'].isoformat(),rows[-1]['transaction_id']]) if more else None
            return BankPage(items=[BankTransaction(**{k:v for k,v in r.items() if k not in ('amount_cents','transaction_date')},amount=money(r['amount_cents']),transaction_date=r['transaction_date'].isoformat()) for r in rows],next_cursor=next_cursor)

    def rules(self,user,company,month,topic):
        month_bounds(month)
        if topic not in ('amount','purpose','bank'):raise BusinessError('VALIDATION_ERROR')
        with self.read_transaction() as tx:
            self.principal(tx,user,company)
            return resolve(tx.knowledge.candidates(company,topic),month,topic)

    def check(self,user,company,month):
        start,end=month_bounds(month)
        with self.read_transaction() as tx:
            self.principal(tx,user,company)
            resolution=resolve(tx.knowledge.candidates(company,'purpose'),month,'purpose')
            status={'resolved':'checked','missing':'insufficient_rules','conflict':'rule_conflict','unsupported':'unsupported'}[resolution.resolution_status]
            missing=None
            if status=='checked':
                policy=resolution.rules[0].policy
                if policy.kind not in ('all','amount_gte'):status='unsupported'
                else:
                    rows=tx.ledger.invoices([company],company=company,start=start,end=end)
                    missing=[MissingInvoice(company_id=company,invoice_id=r['invoice_id'],amount=money(r['amount_cents']),purpose=r['purpose'],note=r['note']) for r in rows if requires_purpose(r['amount_cents'],policy) and is_blank(r['purpose'])]
            return Check(company_id=company,business_month=month,queried_at=utc_now(),rule_refs=resolution.rule_refs,
                check_status=status,missing=missing,count=len(missing) if missing is not None else None)
