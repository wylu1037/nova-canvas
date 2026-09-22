"""QRunnable 任务：在线程池里跑协程，通过信号回传结果。网络调用绝不进 UI 线程。"""
import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    started = Signal()
    finished = Signal(object)  # ImageResponse
    error = Signal(str)


class ApiTask(QRunnable):
    """接收一个协程工厂；每个任务独立 event loop，避免跨线程共享 loop。"""

    def __init__(self, coro_factory: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        super().__init__()
        self._factory = coro_factory
        self.signals = WorkerSignals()
        # 由提交方持有引用直到信号送达，避免跨线程排队信号随对象销毁而丢失
        self.setAutoDelete(False)

    @Slot()
    def run(self) -> None:
        self.signals.started.emit()
        try:
            result = asyncio.run(self._factory())
        except Exception as exc:  # noqa: BLE001 — 统一转为用户可读错误
            logger.warning("后台任务失败: %s", exc)
            self.signals.error.emit(str(exc))
        else:
            self.signals.finished.emit(result)
