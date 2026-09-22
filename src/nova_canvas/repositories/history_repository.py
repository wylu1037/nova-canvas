"""历史记录仓储：抽象接口 + JSON 文件实现。"""
import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path

from nova_canvas.schemas.history import HistoryRecord


class HistoryRepository(ABC):
    @abstractmethod
    async def add(self, record: HistoryRecord) -> None: ...

    @abstractmethod
    async def get(self, record_id: str) -> HistoryRecord | None: ...

    @abstractmethod
    async def list(self, limit: int, offset: int) -> tuple[list[HistoryRecord], int]: ...

    @abstractmethod
    async def delete(self, record_id: str) -> bool: ...


class JsonFileHistoryRepository(HistoryRepository):
    """单文件 JSON 存储；用锁串行化写入，避免并发写坏文件。"""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text("utf-8"))
        except json.JSONDecodeError:
            return []

    def _save(self, items: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(self._path)  # 原子替换

    async def add(self, record: HistoryRecord) -> None:
        async with self._lock:
            items = self._load()
            items.append(record.model_dump(mode="json"))
            await asyncio.to_thread(self._save, items)

    async def get(self, record_id: str) -> HistoryRecord | None:
        for item in self._load():
            if item.get("id") == record_id:
                return HistoryRecord.model_validate(item)
        return None

    async def list(self, limit: int, offset: int) -> tuple[list[HistoryRecord], int]:
        items = list(reversed(self._load()))  # 新的在前
        page = [HistoryRecord.model_validate(i) for i in items[offset : offset + limit]]
        return page, len(items)

    async def delete(self, record_id: str) -> bool:
        async with self._lock:
            items = self._load()
            kept = [i for i in items if i.get("id") != record_id]
            if len(kept) == len(items):
                return False
            await asyncio.to_thread(self._save, kept)
            return True
