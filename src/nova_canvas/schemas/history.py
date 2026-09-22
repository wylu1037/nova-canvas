from typing import Literal

from pydantic import BaseModel, Field

from nova_canvas.schemas.image import UsageInfo


class HistoryRecord(BaseModel):
    id: str
    kind: Literal["generate", "edit"]
    created: int
    model: str
    prompt: str
    size: str
    output_format: str
    usage: UsageInfo
    file_path: str
    # 编辑任务仅记录输入图数量与来源类型，不存 Base64 正文（体积大且可能含隐私）
    input_images: int = 0
    params: dict = Field(default_factory=dict)


class HistoryPage(BaseModel):
    items: list[HistoryRecord]
    total: int
    limit: int
    offset: int
