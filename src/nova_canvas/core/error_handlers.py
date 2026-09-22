"""FastAPI 全局异常处理器（仅服务端使用；桌面端不导入此模块）。"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from nova_canvas.core.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, request: Request) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", None),
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("业务异常 %s: %s", exc.code, exc.message)
        body = _error_body(exc.code, exc.message, request)
        return JSONResponse(body, status_code=int(exc.status_code))

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        body = _error_body("validation_error", "请求参数校验失败", request)
        # ctx 中可能含原始 ValueError 对象，需转为可序列化结构
        body["error"]["details"] = jsonable_encoder(exc.errors())
        return JSONResponse(body, status_code=422)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理异常")
        return JSONResponse(
            _error_body("internal_error", "服务器内部错误", request),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
