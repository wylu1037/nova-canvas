"""图片生成 / 编辑的请求与响应模型（pydantic v2）。"""
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from nova_canvas.utils.image_utils import is_data_url, validate_size


class ModelName(StrEnum):
    LITE = "sensenova-u1.5-lite"
    FAST = "sensenova-u1.5-fast"


class OutputFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"


class ResponseFormat(StrEnum):
    B64_JSON = "b64_json"
    URL = "url"


Size = Annotated[
    str,
    Field(
        description="'auto' 或 '{W}x{H}'，W/H 为 32 的倍数，范围 512~4096，比例 ≤ 3:1",
        examples=["auto", "2048x2048", "2720x1536"],
    ),
]


class _CommonParams(BaseModel):
    model_config = ConfigDict(use_enum_values=True, str_strip_whitespace=True)

    model: ModelName = Field(default=ModelName.LITE, description="模型名")
    size: Size = "auto"
    # 设计文档建议显式传 watermark 防止上游默认值变更
    watermark: bool = Field(default=True, description="是否添加官方水印")
    response_format: ResponseFormat = Field(default=ResponseFormat.B64_JSON)
    output_format: OutputFormat = Field(default=OutputFormat.PNG)
    prompt_extend: bool = Field(default=True, description="提示词自动润色")
    n: int = Field(default=1, ge=1, le=1, description="上游仅支持 1")

    @field_validator("size")
    @classmethod
    def _check_size(cls, v: str) -> str:
        return validate_size(v)


class GenerateRequest(_CommonParams):
    prompt: str = Field(min_length=1, max_length=4000, description="图像生成描述")

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "model": "sensenova-u1.5-lite",
                    "prompt": "一只在雪山之巅眺望日出的雪豹，电影感光影",
                    "size": "2048x2048",
                    "watermark": False,
                }
            ]
        },
    )


class EditRequest(_CommonParams):
    images: list[str] = Field(
        min_length=1,
        max_length=5,
        description=(
            "第 1 张为主编辑图，其余为参考图；"
            "每项为公网 URL 或 data:image/{fmt};base64,... Data URL"
        ),
    )
    prompt: str = Field(min_length=1, max_length=4000, description="编辑指令")

    @field_validator("images")
    @classmethod
    def _check_images(cls, items: list[str]) -> list[str]:
        for i, v in enumerate(items):
            if v.startswith(("http://", "https://")):
                HttpUrl(v)  # 触发 URL 格式校验
            elif not is_data_url(v):
                raise ValueError(
                    f"images[{i}] 必须是 http(s) URL "
                    "或带 'data:image/{fmt};base64,' 前缀的 Data URL"
                )
        return items


class UsageInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    images_count: int = 1
    input_tokens_details: dict[str, Any] | None = None


class ImageResponse(BaseModel):
    """对外返回：始终包含本地落盘信息；b64 仅在请求方需要时返回。"""

    id: str = Field(description="历史记录 ID")
    created: int
    model: str
    size: str
    output_format: str
    usage: UsageInfo
    file_path: str = Field(description="本地落盘路径")
    download_url: str = Field(description="通过本服务下载图片的相对路径")
    source_url: str | None = Field(default=None, description="上游临时链接（24h 过期），仅供参考")
