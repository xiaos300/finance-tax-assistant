from typing import Annotated
from fastapi import APIRouter,Depends,Request,Query
from app.api.dependencies import user_id,ledger_service
from app.core.contracts import Envelope,Invoice,InvoicePage,BankPage,Totals,Check,RuleResolution,Company,Month,Topic,ErrorEnvelope,Id

router=APIRouter(prefix='/api/v1',tags=['ledger'],responses={status:{'model':ErrorEnvelope} for status in (401,403,404,422,503)})
Limit=Annotated[int,Query(ge=1,le=100)]
Cursor=Annotated[str | None,Query(min_length=1,max_length=2000)]


def wrap(request,data):return Envelope(data=data,request_id=request.state.request_id)


@router.get('/invoices/search',response_model=Envelope[InvoicePage])
def search(request:Request,q:Annotated[str,Query(max_length=500)]='',company_id:Company | None=None,
           business_month:Month | None=None,cursor:Cursor=None,limit:Limit=20,user=Depends(user_id),service=Depends(ledger_service)):
    return wrap(request,service.search(user,company_id,business_month,q,cursor,limit))


@router.get('/companies/{company_id}/invoices/{invoice_id}',response_model=Envelope[Invoice])
def invoice(request:Request,company_id:Company,invoice_id:Id,user=Depends(user_id),service=Depends(ledger_service)):
    return wrap(request,service.invoice(user,company_id,invoice_id))


@router.get('/companies/{company_id}/totals',response_model=Envelope[Totals],response_model_exclude_unset=True)
def totals(request:Request,company_id:Company,business_month:Month,metrics:str | None=None,user=Depends(user_id),service=Depends(ledger_service)):
    return wrap(request,service.totals(user,company_id,business_month,metrics))


@router.get('/companies/{company_id}/bank-transactions',response_model=Envelope[BankPage])
def banks(request:Request,company_id:Company,business_month:Month,cursor:Cursor=None,limit:Limit=20,user=Depends(user_id),service=Depends(ledger_service)):
    return wrap(request,service.banks(user,company_id,business_month,cursor,limit))


@router.get('/companies/{company_id}/purpose-check',response_model=Envelope[Check])
def check(request:Request,company_id:Company,business_month:Month,user=Depends(user_id),service=Depends(ledger_service)):
    return wrap(request,service.check(user,company_id,business_month))


@router.get('/companies/{company_id}/rules',response_model=Envelope[RuleResolution])
def rules(request:Request,company_id:Company,business_month:Month,topic:Topic,user=Depends(user_id),service=Depends(ledger_service)):
    return wrap(request,service.rules(user,company_id,business_month,topic))
