from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    api_key_configured: bool


class SizePreset(BaseModel):
    size: str
    ratio: str
    tier: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: list | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
