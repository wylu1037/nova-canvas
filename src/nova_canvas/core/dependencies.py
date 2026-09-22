"""依赖注入：单例挂在 app.state（lifespan 创建），按请求组装 service。"""
from typing import Annotated

from fastapi import Depends, Request

from nova_canvas.clients.sensenova import SenseNovaClient
from nova_canvas.core.config import Settings, get_settings
from nova_canvas.core.exceptions import ConfigurationError
from nova_canvas.repositories.history_repository import HistoryRepository
from nova_canvas.repositories.image_storage import ImageStorage
from nova_canvas.services.history_service import HistoryService
from nova_canvas.services.image_service import ImageService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_client(request: Request, settings: SettingsDep) -> SenseNovaClient:
    if not settings.api_key_configured:
        raise ConfigurationError("未配置 SENSENOVA_API_KEY，请在环境变量或 .env 中设置")
    return request.app.state.client


def get_storage(request: Request) -> ImageStorage:
    return request.app.state.storage


def get_history_repo(request: Request) -> HistoryRepository:
    return request.app.state.history_repo


def get_image_service(
    client: Annotated[SenseNovaClient, Depends(get_client)],
    storage: Annotated[ImageStorage, Depends(get_storage)],
    history: Annotated[HistoryRepository, Depends(get_history_repo)],
) -> ImageService:
    return ImageService(client, storage, history)


def get_history_service(
    history: Annotated[HistoryRepository, Depends(get_history_repo)],
    storage: Annotated[ImageStorage, Depends(get_storage)],
) -> HistoryService:
    return HistoryService(history, storage)


ImageServiceDep = Annotated[ImageService, Depends(get_image_service)]
HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]
