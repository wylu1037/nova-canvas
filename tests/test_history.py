from httpx import Response

from tests.conftest import BASE, upstream_body


def _make(client, api):
    api.post(f"{BASE}/images/generations").mock(return_value=Response(200, json=upstream_body()))
    return client.post("/api/v1/images/generations", json={"prompt": "p"}).json()["id"]


def test_get_delete_404(client, api, settings):
    rid = _make(client, api)
    assert client.get(f"/api/v1/history/{rid}").status_code == 200
    r = client.delete(f"/api/v1/history/{rid}", params={"remove_file": "true"})
    assert r.status_code == 204
    assert not list(settings.output_dir.glob("*.png"))
    assert client.get(f"/api/v1/history/{rid}").status_code == 404
    assert client.get(f"/api/v1/history/{rid}/image").json()["error"]["code"] == "not_found"


def test_pagination_newest_first(client, api):
    ids = [_make(client, api) for _ in range(3)]
    page = client.get("/api/v1/history", params={"limit": 2}).json()
    assert page["total"] == 3 and [i["id"] for i in page["items"]] == ids[::-1][:2]
