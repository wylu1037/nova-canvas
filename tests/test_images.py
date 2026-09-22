import json

from httpx import Response

from tests.conftest import BASE, CDN_URL, png_bytes, upstream_body


def test_generate_b64_persists_and_records(client, api, settings):
    route = api.post(f"{BASE}/images/generations").mock(
        return_value=Response(200, json=upstream_body()))
    r = client.post("/api/v1/images/generations",
                    json={"prompt": "雪豹", "size": "2048x2048", "watermark": False})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["usage"]["total_tokens"] == 30
    assert body["file_path"].endswith(".png")
    assert "X-Request-ID" in r.headers

    sent = json.loads(route.calls.last.request.content)
    assert sent["model"] == "sensenova-u1.5-lite"
    assert sent["watermark"] is False  # 显式传参
    assert route.calls.last.request.headers["Authorization"] == "Bearer sk-test"

    # 落盘 + 历史
    assert list(settings.output_dir.glob("*.png"))
    hist = client.get("/api/v1/history").json()
    assert hist["total"] == 1 and hist["items"][0]["prompt"] == "雪豹"
    img = client.get(body["download_url"])
    assert img.status_code == 200 and img.content == png_bytes()


def test_edit_url_result_is_downloaded_immediately(client, api):
    api.post(f"{BASE}/images/edits").mock(return_value=Response(200, json=upstream_body(b64=False)))
    dl = api.get(CDN_URL).mock(return_value=Response(200, content=png_bytes()))
    data_url = "data:image/png;base64," + "AAAA"
    r = client.post("/api/v1/images/edits", json={
        "images": [data_url, "https://example.com/ref.jpg"], "prompt": "换成夜景",
        "response_format": "url",
    })
    assert r.status_code == 201, r.text
    assert dl.called
    assert r.json()["source_url"] == CDN_URL
    rec = client.get("/api/v1/history").json()["items"][0]
    assert rec["kind"] == "edit" and rec["input_images"] == 2
    assert "images" not in rec["params"]  # 不存 Base64 正文


def test_edit_upload_converts_to_data_url(client, api):
    route = api.post(f"{BASE}/images/edits").mock(return_value=Response(200, json=upstream_body()))
    r = client.post("/api/v1/images/edits/upload",
                    data={"prompt": "加个帽子"},
                    files=[("images", ("a.png", png_bytes(), "image/png"))])
    assert r.status_code == 201, r.text
    sent = json.loads(route.calls.last.request.content)
    assert sent["images"][0]["image_url"].startswith("data:image/png;base64,")


def test_edit_requires_valid_images(client):
    r = client.post("/api/v1/images/edits", json={"images": [], "prompt": "x"})
    assert r.status_code == 422
    r = client.post("/api/v1/images/edits", json={"images": ["just-base64=="], "prompt": "x"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_invalid_size_rejected(client):
    for bad in ("100x100", "2050x2048", "4096x1024", "abc"):
        r = client.post("/api/v1/images/generations", json={"prompt": "p", "size": bad})
        assert r.status_code == 422, bad


def test_retry_then_success(client, api):
    route = api.post(f"{BASE}/images/generations").mock(side_effect=[
        Response(503, json={"error": {"message": "busy"}}),
        Response(200, json=upstream_body()),
    ])
    r = client.post("/api/v1/images/generations", json={"prompt": "p"})
    assert r.status_code == 201 and route.call_count == 2


def test_rate_limit_exhausted_maps_to_429(client, api):
    api.post(f"{BASE}/images/generations").mock(return_value=Response(429, json={}))
    r = client.post("/api/v1/images/generations", json={"prompt": "p"})
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"


def test_upstream_400_not_retried_and_key_redacted(client, api):
    route = api.post(f"{BASE}/images/generations").mock(
        return_value=Response(400, json={"error": {"message": "bad key sk-test"}}))
    r = client.post("/api/v1/images/generations", json={"prompt": "p"})
    assert r.status_code == 400 and route.call_count == 1
    assert "sk-test" not in r.text and "[REDACTED]" in r.json()["error"]["message"]


def test_missing_api_key_returns_503(settings, monkeypatch):
    from fastapi.testclient import TestClient
    from pydantic import SecretStr

    from nova_canvas.core.config import get_settings
    from nova_canvas.main import create_app

    s = settings.model_copy(update={"sensenova_api_key": SecretStr("")})
    app = create_app(s)
    app.dependency_overrides[get_settings] = lambda: s
    with TestClient(app) as c:
        assert c.get("/api/v1/health").json()["api_key_configured"] is False
        r = c.post("/api/v1/images/generations", json={"prompt": "p"})
        assert r.status_code == 503 and r.json()["error"]["code"] == "not_configured"


def test_presets_and_docs(client):
    assert len(client.get("/api/v1/images/presets").json()) == 6
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200
