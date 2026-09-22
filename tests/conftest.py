import base64
import io
from pathlib import Path

import pytest
import respx
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import SecretStr

from nova_canvas.core.config import Settings, get_settings
from nova_canvas.main import create_app

BASE = "https://api.test/v1"
CDN_URL = "https://cdn.test/gen/img.png"


def png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buf, format="PNG")
    return buf.getvalue()


def upstream_body(*, b64: bool = True) -> dict:
    item = {"b64_json": base64.b64encode(png_bytes()).decode()} if b64 else {"url": CDN_URL}
    return {
        "created": 1788851674,
        "data": [item],
        "output_format": "png",
        "size": "2048x2048",
        "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30, "images_count": 1},
    }


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        SENSENOVA_API_KEY=SecretStr("sk-test"),
        NOVA_BASE_URL=BASE,
        NOVA_OUTPUT_DIR=tmp_path / "out",
        NOVA_HISTORY_FILE=tmp_path / "out" / "history.json",
        NOVA_MAX_RETRIES=2,
    )


@pytest.fixture
def client(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    # 让退避不真正 sleep
    import nova_canvas.clients.sensenova as mod
    monkeypatch.setattr(mod.SenseNovaClient, "_backoff", staticmethod(lambda _a: 0))
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        yield c


@pytest.fixture
def api():
    with respx.mock(assert_all_called=False) as mock:
        yield mock
