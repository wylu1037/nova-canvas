from pathlib import Path

from nova_canvas.core.exceptions import NotFoundError
from nova_canvas.repositories.history_repository import HistoryRepository
from nova_canvas.repositories.image_storage import ImageStorage
from nova_canvas.schemas.history import HistoryPage, HistoryRecord


class HistoryService:
    def __init__(self, history: HistoryRepository, storage: ImageStorage) -> None:
        self._history = history
        self._storage = storage

    async def list(self, limit: int, offset: int) -> HistoryPage:
        items, total = await self._history.list(limit, offset)
        return HistoryPage(items=items, total=total, limit=limit, offset=offset)

    async def get(self, record_id: str) -> HistoryRecord:
        rec = await self._history.get(record_id)
        if rec is None:
            raise NotFoundError(f"历史记录 {record_id} 不存在")
        return rec

    async def image_path(self, record_id: str) -> Path:
        rec = await self.get(record_id)
        path = self._storage.resolve(rec.file_path)
        if path is None:
            raise NotFoundError("图片文件不存在或已被删除")
        return path

    async def delete(self, record_id: str, remove_file: bool) -> None:
        rec = await self.get(record_id)
        if remove_file and (p := self._storage.resolve(rec.file_path)):
            p.unlink(missing_ok=True)
        await self._history.delete(record_id)
