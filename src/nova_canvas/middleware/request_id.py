import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from nova_canvas.core.logging import request_id_ctx

HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """为每个请求分配/透传 X-Request-ID，并注入日志上下文。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get(HEADER) or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers[HEADER] = rid
        return response
