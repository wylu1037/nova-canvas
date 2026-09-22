import pytest

from nova_canvas.utils.image_utils import strip_data_url, to_data_url, validate_size
from tests.conftest import png_bytes


@pytest.mark.parametrize("ok", ["auto", "2048x2048", "2720x1536", "512x1536", "4096x4096"])
def test_valid_sizes(ok):
    assert validate_size(ok) == ok


@pytest.mark.parametrize("bad", ["511x512", "4128x4096", "2000x2000", "1536x4608", "2048"])
def test_invalid_sizes(bad):
    with pytest.raises(ValueError):
        validate_size(bad)


def test_data_url_roundtrip():
    url = to_data_url(png_bytes())
    assert url.startswith("data:image/png;base64,")
    assert strip_data_url(url) == url.split(",", 1)[1]
    assert strip_data_url("plain") == "plain"
