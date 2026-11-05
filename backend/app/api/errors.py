from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.contracts import ErrorBody, ErrorEnvelope
from app.core.exceptions import BusinessError
from app.infrastructure.database.targets import TargetError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError


def error_response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    body = ErrorEnvelope(error=ErrorBody(code=code, message=message, details={},
                                       retryable=status == 503, turn_id=None),
                         request_id=request.state.request_id)
    return JSONResponse(body.model_dump(mode="json"), status_code=status)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def business_error(request:Request,exc:BusinessError):
        return error_response(request,exc.status,exc.code,exc.message)

    async def storage_error(request:Request,exc:Exception):
        return error_response(request,503,'STORAGE_UNAVAILABLE','当前数据暂时无法读取')
    for kind in (SQLAlchemyError,TargetError,ValidationError):
        app.add_exception_handler(kind,storage_error)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error_response(request, exc.status_code, "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR", "请求无法处理")

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        malformed = any(item["type"] == "json_invalid" for item in exc.errors())
        return error_response(request, 400 if malformed else 422, "VALIDATION_ERROR", "请求格式或参数无效")

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return error_response(request, 500, "INTERNAL_ERROR", "服务暂时无法处理请求")
