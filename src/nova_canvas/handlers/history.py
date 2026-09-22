from fastapi import APIRouter, Query, status
from fastapi.responses import FileResponse

from nova_canvas.core.dependencies import HistoryServiceDep
from nova_canvas.schemas.common import ErrorResponse
from nova_canvas.schemas.history import HistoryPage, HistoryRecord

router = APIRouter(prefix="/history", tags=["history"])
_NOT_FOUND = {404: {"model": ErrorResponse}}


@router.get("", response_model=HistoryPage, summary="历史记录列表（新的在前）")
async def list_history(
    service: HistoryServiceDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> HistoryPage:
    return await service.list(limit, offset)


@router.get("/{record_id}", response_model=HistoryRecord, responses=_NOT_FOUND, summary="历史详情")
async def get_history(record_id: str, service: HistoryServiceDep) -> HistoryRecord:
    return await service.get(record_id)


@router.get(
    "/{record_id}/image",
    response_class=FileResponse,
    responses={200: {"content": {"image/*": {}}}, **_NOT_FOUND},
    summary="下载结果图片（读本地文件，不依赖 24h 临时链接）",
)
async def get_image(record_id: str, service: HistoryServiceDep) -> FileResponse:
    path = await service.image_path(record_id)
    return FileResponse(path, filename=path.name)


@router.delete(
    "/{record_id}", status_code=status.HTTP_204_NO_CONTENT, responses=_NOT_FOUND, summary="删除记录"
)
async def delete_history(
    record_id: str,
    service: HistoryServiceDep,
    remove_file: bool = Query(False, description="是否同时删除本地图片文件"),
) -> None:
    await service.delete(record_id, remove_file)
