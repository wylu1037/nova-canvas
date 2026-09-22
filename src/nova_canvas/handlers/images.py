from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from nova_canvas.core.dependencies import ImageServiceDep
from nova_canvas.schemas.common import ErrorResponse, SizePreset
from nova_canvas.schemas.image import (
    EditRequest,
    GenerateRequest,
    ImageResponse,
    ModelName,
    OutputFormat,
    ResponseFormat,
)
from nova_canvas.utils.image_utils import SIZE_PRESETS, to_data_url

router = APIRouter(prefix="/images", tags=["images"])

_ERRORS = {
    400: {"model": ErrorResponse, "description": "上游拒绝请求（图片无法访问/参数非法）"},
    401: {"model": ErrorResponse, "description": "API Key 无效"},
    429: {"model": ErrorResponse, "description": "限流，请稍后重试"},
    502: {"model": ErrorResponse, "description": "上游服务错误"},
    503: {"model": ErrorResponse, "description": "服务未配置 API Key"},
}


@router.post(
    "/generations",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="文生图",
    description="根据提示词生成一张图片，结果自动落盘并写入历史记录。",
    responses=_ERRORS,
)
async def generate(req: GenerateRequest, service: ImageServiceDep) -> ImageResponse:
    return await service.generate(req)


@router.post(
    "/edits",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="图片编辑（JSON）",
    description="images[0] 为主编辑图，其余为参考图（共至多 5 张）；每项为公网 URL 或 Data URL。",
    responses=_ERRORS,
)
async def edit(req: EditRequest, service: ImageServiceDep) -> ImageResponse:
    return await service.edit(req)


@router.post(
    "/edits/upload",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="图片编辑（文件上传）",
    description="multipart 上传本地图片，服务端自动转为带前缀的 Data URL 后调用编辑接口。",
    responses=_ERRORS,
)
async def edit_upload(
    service: ImageServiceDep,
    prompt: Annotated[str, Form(min_length=1, description="编辑指令")],
    images: Annotated[list[UploadFile], File(description="第 1 张为主图，最多 5 张")],
    model: Annotated[ModelName, Form()] = ModelName.LITE,
    size: Annotated[str, Form()] = "auto",
    watermark: Annotated[bool, Form()] = True,
    output_format: Annotated[OutputFormat, Form()] = OutputFormat.PNG,
    response_format: Annotated[ResponseFormat, Form()] = ResponseFormat.B64_JSON,
    prompt_extend: Annotated[bool, Form()] = True,
) -> ImageResponse:
    data_urls = [to_data_url(await f.read()) for f in images]
    req = EditRequest(
        images=data_urls, prompt=prompt, model=model, size=size, watermark=watermark,
        output_format=output_format, response_format=response_format, prompt_extend=prompt_extend,
    )
    return await service.edit(req)


@router.get("/presets", response_model=list[SizePreset], summary="推荐尺寸预设")
async def presets() -> list[SizePreset]:
    return [SizePreset(size=s, **meta) for s, meta in SIZE_PRESETS.items()]
