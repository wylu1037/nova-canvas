import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("nova_canvas.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    """记录方法、路径、状态码、耗时；不记录请求体（可能含 Base64 图片与提示词）。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.error("%s %s -> 500 %.0fms", request.method, request.url.path,
                         (time.perf_counter() - start) * 1000)
            raise
        elapsed = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %d %.0fms", request.method, request.url.path,
                    response.status_code, elapsed)
        response.headers["X-Process-Time-Ms"] = f"{elapsed:.0f}"
        return response
