from fastapi import APIRouter,Depends,Request
from app.api.dependencies import user_id,ledger_service
from app.core.contracts import Envelope,Principal,ErrorEnvelope

router=APIRouter(prefix='/api/v1',tags=['identity'],responses={status:{'model':ErrorEnvelope} for status in (401,403,404,422,503)})


@router.get('/me',response_model=Envelope[Principal])
def me(request:Request,user=Depends(user_id),service=Depends(ledger_service)):
    return Envelope(data=service.me(user),request_id=request.state.request_id)
