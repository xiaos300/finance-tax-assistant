from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.contracts import Envelope, Health

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/live", response_model=Envelope[Health])
def live(request: Request):
    return Envelope(data=Health(status="alive"), request_id=request.state.request_id)


@router.get("/ready", response_model=Envelope[Health], responses={503: {"model": Envelope[Health]}})
def ready(request: Request):
    # D0 has no schema/seed/singleton preparation. Never infer readiness from SELECT 1.
    body = Envelope(data=Health(status="not_ready", checks={"database_prepared": False}),
                    request_id=request.state.request_id)
    return JSONResponse(body.model_dump(mode="json"), status_code=503)
