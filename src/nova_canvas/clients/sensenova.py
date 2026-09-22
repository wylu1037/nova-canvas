"""SenseNova API 客户端：鉴权、指数退避重试、错误脱敏、结果统一解码为字节。"""
import asyncio
import base64
import logging
import random
from dataclasses import dataclass, field
from typing import Any

import httpx

from nova_canvas.core.exceptions import SenseNovaError
from nova_canvas.utils.image_utils import strip_data_url

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass
class RawImageResult:
    image_bytes: bytes
    size: str
    output_format: str
    created: int
    usage: dict[str, Any] = field(default_factory=dict)
    source_url: str | None = None


class SenseNovaClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://token.sensenova.cn/v1",
        timeout: float = 120.0,
        max_retries: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._max_retries = max_retries
        # 生成/编辑耗时长：read 放宽，connect 收紧
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(connect=10.0, read=timeout, write=30.0, pool=10.0),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    # ---- 公开方法 ----------------------------------------------------------

    async def generate(self, payload: dict[str, Any]) -> RawImageResult:
        raw = await self._post("/images/generations", payload)
        return await self._to_result(raw)

    async def edit(self, payload: dict[str, Any]) -> RawImageResult:
        raw = await self._post("/images/edits", payload)
        return await self._to_result(raw)

    # ---- 内部实现 ----------------------------------------------------------

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: str = "请求重试后仍失败"
        last_status: int | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                resp = await self._http.post(path, json=payload)
            except httpx.HTTPError as exc:
                last_error = f"网络请求失败：{type(exc).__name__}"
                logger.warning("POST %s 第 %d 次网络错误: %s", path, attempt, type(exc).__name__)
            else:
                if resp.is_success:
                    return resp.json()
                last_status = resp.status_code
                last_error = self._fmt_error(resp)
                if resp.status_code not in RETRYABLE_STATUS:
                    raise SenseNovaError(last_error, upstream_status=resp.status_code)
                logger.warning("POST %s 第 %d 次返回 %d，准备重试", path, attempt, resp.status_code)

            if attempt < self._max_retries:
                await asyncio.sleep(self._backoff(attempt))

        if last_status == 429:
            last_error = "请求过于频繁，请稍后重试"
        raise SenseNovaError(last_error, upstream_status=last_status)

    @staticmethod
    def _backoff(attempt: int) -> float:
        """指数退避 + 抖动：1s, 2s, 4s ..."""
        return min(2 ** (attempt - 1), 16) + random.uniform(0, 0.5)

    async def _to_result(self, raw: dict[str, Any]) -> RawImageResult:
        try:
            item = raw["data"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise SenseNovaError("上游响应缺少 data 字段") from exc

        source_url: str | None = None
        if item.get("b64_json"):
            try:
                data = base64.b64decode(strip_data_url(item["b64_json"]))
            except ValueError as exc:
                raise SenseNovaError("上游返回的 Base64 无法解码") from exc
        elif item.get("url"):
            source_url = item["url"]
            data = await self._download(source_url)  # 24h 过期，立即下载
        else:
            raise SenseNovaError("上游响应既无 b64_json 也无 url")

        return RawImageResult(
            image_bytes=data,
            size=raw.get("size", ""),
            output_format=raw.get("output_format", "png"),
            created=int(raw.get("created", 0)),
            usage=raw.get("usage", {}),
            source_url=source_url,
        )

    async def _download(self, url: str) -> bytes:
        try:
            # 结果 CDN 与 API 不同域，需绝对 URL；不带鉴权头
            resp = await self._http.get(url, headers={"Authorization": ""})
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise SenseNovaError(f"下载结果图片失败：{type(exc).__name__}") from exc
        return resp.content

    def _fmt_error(self, resp: httpx.Response) -> str:
        try:
            body = resp.json()
            msg = (body.get("error") or {}).get("message") or body.get("message") or ""
        except ValueError:
            msg = resp.text[:300]
        if self._api_key:
            msg = msg.replace(self._api_key, "[REDACTED]")
        return f"API 错误 HTTP {resp.status_code}: {msg}"
