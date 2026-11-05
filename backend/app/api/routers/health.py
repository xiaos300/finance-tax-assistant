from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.contracts import Envelope, Health

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/live", response_model=Envelope[Health])
def live(request: Request):
    return Envelope(data=Health(status="alive"), request_id=request.state.request_id)


@router.get("/ready", response_model=Envelope[Health], responses={503: {"model": Envelope[Health]}})
def ready(request: Request):
    prepared=False
    try:
        from app.api.dependencies import ledger_service
        from app.infrastructure.database.maintenance import inspect_prepared
        ledger_service(request)
        with request.app.state.database_engine.connect() as connection:
            inspect_prepared(connection)
        prepared=True
    except Exception:
        pass
    body = Envelope(data=Health(status="ready" if prepared else "not_ready", checks={"database_prepared": prepared}),
                    request_id=request.state.request_id)
    return JSONResponse(body.model_dump(mode="json"), status_code=200 if prepared else 503)
