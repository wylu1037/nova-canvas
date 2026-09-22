"""图片文件存储：结果字节落盘到 output/{timestamp}_{model}.{ext}。"""
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class ImageStorage(ABC):
    @abstractmethod
    async def save(self, image_bytes: bytes, model: str, ext: str) -> Path: ...

    @abstractmethod
    def resolve(self, file_path: str) -> Path | None:
        """把记录中的路径解析为存在的本地文件，防止目录穿越。"""


class LocalImageStorage(ImageStorage):
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir.resolve()
        self._dir.mkdir(parents=True, exist_ok=True)

    async def save(self, image_bytes: bytes, model: str, ext: str) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_model = model.replace("/", "_")
        path = self._dir / f"{ts}_{safe_model}.{ext}"
        await asyncio.to_thread(path.write_bytes, image_bytes)
        return path

    def resolve(self, file_path: str) -> Path | None:
        p = Path(file_path).resolve()
        if p.is_file() and p.is_relative_to(self._dir):
            return p
        return None
