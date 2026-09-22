"""统一业务异常。纯 Python，不依赖任何 Web 框架，桌面端与服务端共用。"""
from http import HTTPStatus


class AppError(Exception):
    """所有业务异常的基类；message 对用户可读且已脱敏。"""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "not_configured"


class SenseNovaError(AppError):
    """上游 API 返回的错误。"""

    status_code = HTTPStatus.BAD_GATEWAY
    code = "upstream_error"

    def __init__(self, message: str, upstream_status: int | None = None) -> None:
        super().__init__(message)
        self.upstream_status = upstream_status
        if upstream_status == 429:
            self.status_code = HTTPStatus.TOO_MANY_REQUESTS
            self.code = "rate_limited"
        elif upstream_status in (400, 422):
            self.status_code = HTTPStatus.BAD_REQUEST
            self.code = "upstream_rejected"
        elif upstream_status in (401, 403):
            self.status_code = HTTPStatus.UNAUTHORIZED
            self.code = "upstream_unauthorized"


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"
