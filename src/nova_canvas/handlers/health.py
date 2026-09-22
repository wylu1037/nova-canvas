from fastapi import APIRouter

from nova_canvas.core.dependencies import SettingsDep
from nova_canvas.schemas.common import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok", version=settings.app_version, api_key_configured=settings.api_key_configured
    )
