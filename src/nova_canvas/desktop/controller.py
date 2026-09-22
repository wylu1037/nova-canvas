"""控制层：提交任务、结果分发、状态管理。UI 只与 Controller 的信号/方法交互。"""
import asyncio
import logging
from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, Signal

from nova_canvas.clients.sensenova import SenseNovaClient
from nova_canvas.core.exceptions import AppError
from nova_canvas.desktop.config import ConfigStore
from nova_canvas.repositories.history_repository import JsonFileHistoryRepository
from nova_canvas.repositories.image_storage import LocalImageStorage
from nova_canvas.schemas.history import HistoryRecord
from nova_canvas.schemas.image import EditRequest, GenerateRequest, ImageResponse
from nova_canvas.services.image_service import ImageService

from .workers import ApiTask

logger = logging.getLogger(__name__)


class AppController(QObject):
    task_started = Signal(str)          # "generate" | "edit"
    task_finished = Signal(object)      # ImageResponse
    task_failed = Signal(str)           # 脱敏后的错误消息
    history_changed = Signal()

    def __init__(self, config: ConfigStore, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._pool = QThreadPool.globalInstance()
        self._busy = False
        self._task: ApiTask | None = None

    @property
    def busy(self) -> bool:
        return self._busy

    @property
    def configured(self) -> bool:
        return bool(self.config.api_key)

    # ---- 提交 -------------------------------------------------------------------

    def submit_generate(self, req: GenerateRequest) -> None:
        self._submit("generate", lambda svc: svc.generate(req))

    def submit_edit(self, req: EditRequest) -> None:
        self._submit("edit", lambda svc: svc.edit(req))

    def _submit(self, kind: str, call) -> None:
        if self._busy:
            return
        if not self.configured:
            self.task_failed.emit("未配置 API Key，请先打开设置")
            return
        settings = self.config.to_settings()

        async def job() -> ImageResponse:
            # 每个任务新建客户端：绑定到本任务的 loop，且设置变更即时生效
            client = SenseNovaClient(
                api_key=settings.sensenova_api_key.get_secret_value(),
                base_url=settings.base_url,
                timeout=settings.request_timeout,
                max_retries=settings.max_retries,
            )
            try:
                svc = ImageService(
                    client,
                    LocalImageStorage(settings.output_dir),
                    JsonFileHistoryRepository(settings.history_file),
                )
                return await call(svc)
            finally:
                await client.aclose()

        task = ApiTask(job)
        task.signals.finished.connect(self._on_finished)
        task.signals.error.connect(self._on_error)
        self._task = task
        self._busy = True
        self.task_started.emit(kind)
        self._pool.start(task)

    def _on_finished(self, result: ImageResponse) -> None:
        self._busy = False
        self._task = None
        self.task_finished.emit(result)
        self.history_changed.emit()

    def _on_error(self, message: str) -> None:
        self._busy = False
        self._task = None
        self.task_failed.emit(message)

    # ---- 历史（读文件很快，直接在 UI 线程同步调用） --------------------------------

    def _repo(self) -> JsonFileHistoryRepository:
        return JsonFileHistoryRepository(self.config.to_settings().history_file)

    def list_history(self, limit: int = 200) -> list[HistoryRecord]:
        items, _ = asyncio.run(self._repo().list(limit, 0))
        return items

    def delete_history(self, record_id: str, remove_file: bool) -> None:
        rec = asyncio.run(self._repo().get(record_id))
        if rec and remove_file:
            Path(rec.file_path).unlink(missing_ok=True)
        asyncio.run(self._repo().delete(record_id))
        self.history_changed.emit()

    @staticmethod
    def read_image(path: str) -> bytes:
        try:
            return Path(path).read_bytes()
        except OSError as exc:
            raise AppError(f"无法读取图片文件：{Path(path).name}") from exc
