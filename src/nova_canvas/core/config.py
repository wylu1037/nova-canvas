"""应用配置：环境变量 > .env 文件 > 默认值。"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 密钥不带前缀，与设计文档中的 SENSENOVA_API_KEY 保持一致
    sensenova_api_key: SecretStr = Field(default=SecretStr(""), alias="SENSENOVA_API_KEY")

    base_url: str = Field(default="https://token.sensenova.cn/v1", alias="NOVA_BASE_URL")
    request_timeout: float = Field(default=120.0, alias="NOVA_REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, ge=1, le=5, alias="NOVA_MAX_RETRIES")

    output_dir: Path = Field(default=Path("./output"), alias="NOVA_OUTPUT_DIR")
    history_file: Path = Field(default=Path("./output/history.json"), alias="NOVA_HISTORY_FILE")

    log_level: str = Field(default="INFO", alias="NOVA_LOG_LEVEL")
    app_name: str = "NovaCanvas"
    app_version: str = "0.1.0"

    @field_validator("base_url")
    @classmethod
    def _strip_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def api_key_configured(self) -> bool:
        return bool(self.sensenova_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()
