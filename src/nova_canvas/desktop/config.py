"""ConfigStore：QSettings + 环境变量。密钥优先级：环境变量 > 仅本次会话 > QSettings 持久化。"""
import os
from pathlib import Path

from pydantic import SecretStr
from PySide6.QtCore import QSettings

from nova_canvas.core.config import Settings
from nova_canvas.schemas.image import ModelName, OutputFormat, ResponseFormat

ENV_KEY = "SENSENOVA_API_KEY"


class ConfigStore:
    def __init__(self) -> None:
        self._s = QSettings("NovaCanvas", "NovaCanvas")
        self._session_key: str | None = None  # "仅本次会话记住"

    # ---- 密钥 ---------------------------------------------------------------

    @property
    def api_key(self) -> str:
        return os.environ.get(ENV_KEY) or self._session_key or self._s.value("api_key", "", str)

    @property
    def api_key_from_env(self) -> bool:
        return bool(os.environ.get(ENV_KEY))

    @property
    def api_key_persisted(self) -> bool:
        return bool(self._s.value("api_key", "", str))

    def set_api_key(self, key: str, persist: bool) -> None:
        key = key.strip()
        if persist:
            self._s.setValue("api_key", key)
            self._session_key = None
        else:
            self._session_key = key
            self._s.remove("api_key")

    # ---- 通用 get/set ---------------------------------------------------------

    def _get(self, k: str, default, typ=str):
        return self._s.value(k, default, typ)

    def _set(self, k: str, v) -> None:
        self._s.setValue(k, v)

    base_url = property(
        lambda s: s._get("base_url", "https://token.sensenova.cn/v1"),
        lambda s, v: s._set("base_url", v.rstrip("/")),
    )
    default_model = property(
        lambda s: s._get("model", ModelName.LITE.value), lambda s, v: s._set("model", v)
    )
    default_size = property(
        lambda s: s._get("size", "2048x2048"), lambda s, v: s._set("size", v)
    )
    default_output_format = property(
        lambda s: s._get("output_format", OutputFormat.PNG.value),
        lambda s, v: s._set("output_format", v),
    )
    default_response_format = property(
        lambda s: s._get("response_format", ResponseFormat.B64_JSON.value),
        lambda s, v: s._set("response_format", v),
    )
    watermark = property(
        lambda s: s._get("watermark", False, bool), lambda s, v: s._set("watermark", v)
    )
    prompt_extend = property(
        lambda s: s._get("prompt_extend", True, bool), lambda s, v: s._set("prompt_extend", v)
    )
    output_dir = property(
        lambda s: Path(s._get("output_dir", str(Path.cwd() / "output"))),
        lambda s, v: s._set("output_dir", str(v)),
    )

    # ---- 转换为服务层配置 -------------------------------------------------------

    def to_settings(self) -> Settings:
        out = self.output_dir
        return Settings(
            SENSENOVA_API_KEY=SecretStr(self.api_key),
            NOVA_BASE_URL=self.base_url,
            NOVA_OUTPUT_DIR=out,
            NOVA_HISTORY_FILE=out / "history.json",
        )
