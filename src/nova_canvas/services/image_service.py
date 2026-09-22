"""图片服务：编排 客户端调用 → 落盘 → 写历史。"""
import logging
import time
import uuid

from nova_canvas.clients.sensenova import RawImageResult, SenseNovaClient
from nova_canvas.repositories.history_repository import HistoryRepository
from nova_canvas.repositories.image_storage import ImageStorage
from nova_canvas.schemas.history import HistoryRecord
from nova_canvas.schemas.image import EditRequest, GenerateRequest, ImageResponse, UsageInfo
from nova_canvas.utils.image_utils import is_data_url

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(
        self,
        client: SenseNovaClient,
        storage: ImageStorage,
        history: HistoryRepository,
    ) -> None:
        self._client = client
        self._storage = storage
        self._history = history

    async def generate(self, req: GenerateRequest) -> ImageResponse:
        payload = req.model_dump()
        logger.info("生成请求 model=%s size=%s prompt_len=%d", req.model, req.size, len(req.prompt))
        result = await self._client.generate(payload)
        return await self._persist("generate", req, result, input_images=0)

    async def edit(self, req: EditRequest) -> ImageResponse:
        payload = req.model_dump()
        payload["images"] = [{"image_url": u} for u in req.images]
        data_urls = sum(1 for u in req.images if is_data_url(u))
        logger.info(
            "编辑请求 model=%s images=%d(data_url=%d) size=%s",
            req.model, len(req.images), data_urls, req.size,
        )
        result = await self._client.edit(payload)
        return await self._persist("edit", req, result, input_images=len(req.images))

    async def _persist(
        self,
        kind: str,
        req: GenerateRequest | EditRequest,
        result: RawImageResult,
        input_images: int,
    ) -> ImageResponse:
        ext = result.output_format or req.output_format
        path = await self._storage.save(result.image_bytes, req.model, ext)
        record_id = uuid.uuid4().hex
        created = result.created or int(time.time())
        usage = UsageInfo.model_validate(result.usage)

        # 历史中不保存 images 正文（Base64 体积大且可能含隐私）
        params = req.model_dump(exclude={"prompt", "images"})
        record = HistoryRecord(
            id=record_id, kind=kind, created=created, model=req.model,
            prompt=req.prompt, size=result.size or req.size, output_format=ext,
            usage=usage, file_path=str(path), input_images=input_images, params=params,
        )
        await self._history.add(record)
        logger.info("结果已落盘 %s total_tokens=%s", path.name, usage.total_tokens)

        return ImageResponse(
            id=record_id, created=created, model=req.model, size=record.size,
            output_format=ext, usage=usage, file_path=str(path),
            download_url=f"/api/v1/history/{record_id}/image", source_url=result.source_url,
        )
