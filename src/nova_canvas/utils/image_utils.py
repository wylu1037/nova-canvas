"""图片工具：尺寸校验、Data URL 编解码、缩略图。"""
import base64
import io
import re

from PIL import Image

SIZE_MIN, SIZE_MAX, SIZE_STEP, MAX_RATIO = 512, 4096, 32, 3.0
_DATA_URL_RE = re.compile(r"^data:image/(?P<fmt>[a-zA-Z0-9.+-]+);base64,(?P<data>.+)$", re.S)
_SIZE_RE = re.compile(r"^(\d+)x(\d+)$")

# 设计文档 §2.1 推荐预设
SIZE_PRESETS: dict[str, dict] = {
    "2048x2048": {"ratio": "1:1", "tier": "2K"},
    "2720x1536": {"ratio": "16:9", "tier": "2K"},
    "1536x2720": {"ratio": "9:16", "tier": "2K"},
    "2496x1664": {"ratio": "3:2", "tier": "2K"},
    "1664x2496": {"ratio": "2:3", "tier": "2K"},
    "4096x4096": {"ratio": "1:1", "tier": "4K"},
}


def validate_size(size: str) -> str:
    """校验 size：'auto' 或 '{W}x{H}'（32 倍数、512~4096、比例 ≤ 3:1）。

    返回原值，非法抛 ValueError。
    """
    if size == "auto":
        return size
    m = _SIZE_RE.match(size)
    if not m:
        raise ValueError("size 格式必须为 'auto' 或 '{W}x{H}'")
    w, h = int(m.group(1)), int(m.group(2))
    for name, v in (("宽", w), ("高", h)):
        if not SIZE_MIN <= v <= SIZE_MAX:
            raise ValueError(f"{name}必须在 {SIZE_MIN}~{SIZE_MAX} 之间")
        if v % SIZE_STEP:
            raise ValueError(f"{name}必须是 {SIZE_STEP} 的倍数")
    if max(w, h) / min(w, h) > MAX_RATIO:
        raise ValueError("宽高比不能超过 3:1 或 1:3")
    return size


def is_data_url(value: str) -> bool:
    return bool(_DATA_URL_RE.match(value))


def strip_data_url(value: str) -> str:
    """去掉可能的 data:image/...;base64, 前缀，返回纯 Base64。"""
    m = _DATA_URL_RE.match(value)
    return m.group("data") if m else value


def to_data_url(image_bytes: bytes, fmt: str | None = None) -> str:
    """编码为带完整前缀的 Data URL；fmt 未给时用 Pillow 探测。"""
    if fmt is None:
        with Image.open(io.BytesIO(image_bytes)) as im:
            fmt = (im.format or "png").lower()
    fmt = "jpeg" if fmt == "jpg" else fmt
    return f"data:image/{fmt};base64,{base64.b64encode(image_bytes).decode()}"


def sniff_format(image_bytes: bytes) -> str:
    with Image.open(io.BytesIO(image_bytes)) as im:
        fmt = (im.format or "png").lower()
    return "jpg" if fmt == "jpeg" else fmt


def make_thumbnail(image_bytes: bytes, max_side: int = 256) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as im:
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="JPEG", quality=85)
        return buf.getvalue()
