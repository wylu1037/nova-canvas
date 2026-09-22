"""应用工厂与入口。"""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from nova_canvas.clients.sensenova import SenseNovaClient
from nova_canvas.core.config import Settings, get_settings
from nova_canvas.core.error_handlers import register_exception_handlers
from nova_canvas.core.logging import setup_logging
from nova_canvas.handlers import health, history, images
from nova_canvas.middleware.access_log import AccessLogMiddleware
from nova_canvas.middleware.request_id import RequestIdMiddleware
from nova_canvas.repositories.history_repository import JsonFileHistoryRepository
from nova_canvas.repositories.image_storage import LocalImageStorage

logger = logging.getLogger(__name__)

DESCRIPTION = """
NovaCanvas 图片工作台后端：封装 SenseNova U1.5 Lite / Fast 的文生图与图片编辑能力。

- 结果图片**立即落盘**（上游 `url` 仅 24h 有效），预览/下载一律读本地文件
- 自动处理 429/5xx 指数退避重试；错误信息脱敏
- 编辑接口至少 1 张图、至多 5 张；Base64 必须带 `data:image/{fmt};base64,` 前缀
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        app.state.client = SenseNovaClient(
            api_key=settings.sensenova_api_key.get_secret_value(),
            base_url=settings.base_url,
            timeout=settings.request_timeout,
            max_retries=settings.max_retries,
        )
        app.state.storage = LocalImageStorage(settings.output_dir)
        app.state.history_repo = JsonFileHistoryRepository(settings.history_file)
        if not settings.api_key_configured:
            logger.warning("未配置 SENSENOVA_API_KEY，生成/编辑接口将返回 503")
        logger.info("%s v%s 启动，输出目录 %s", settings.app_name, settings.app_version,
                    settings.output_dir)
        try:
            yield
        finally:
            await app.state.client.aclose()

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description=DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    # 中间件按注册逆序执行：RequestId 最外层，先于访问日志生效
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    api = "/api/v1"
    app.include_router(health.router, prefix=api)
    app.include_router(images.router, prefix=api)
    app.include_router(history.router, prefix=api)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("nova_canvas.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
