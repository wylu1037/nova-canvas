"""桌面端离屏测试：不弹窗，验证校验逻辑与后台任务信号。"""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QThreadPool  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from nova_canvas.desktop.ui.edit_tab import EditTab  # noqa: E402
from nova_canvas.desktop.ui.param_panel import CUSTOM, ParamPanel  # noqa: E402
from nova_canvas.desktop.workers import ApiTask  # noqa: E402
from tests.conftest import png_bytes  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_generate_panel_validation(qapp):
    p = ParamPanel("generate")
    assert not p.button.isEnabled()           # 空 prompt
    p.prompt.setPlainText("雪豹")
    assert p.button.isEnabled()
    p.size.setCurrentIndex(p.size.findData(CUSTOM))
    assert not p.button.isEnabled()           # 自定义但未填
    p.w_edit.setText("2000")
    p.h_edit.setText("2000")
    assert not p.button.isEnabled() and "32" in p.custom_hint.text()
    p.w_edit.setText("2048")
    p.h_edit.setText("2048")
    assert p.button.isEnabled() and p.params()["size"] == "2048x2048"
    p.set_busy(True)
    assert not p.button.isEnabled()
    p.set_busy(False)
    assert p.button.isEnabled()


def test_edit_tab_requires_main_image(qapp):
    tab = EditTab()
    tab.set_model("sensenova-u1.5-fast")
    tab.panel.prompt.setPlainText("换成夜景")
    assert not tab.panel.button.isEnabled()   # 无主图 → 禁用
    tab.set_main_image(png_bytes())
    assert tab.panel.button.isEnabled()
    got = []
    tab.submit.connect(got.append)
    tab.panel.button.click()
    assert got and got[0].images[0].startswith("data:image/png;base64,")
    assert got[0].model == "sensenova-u1.5-fast"


def test_api_task_emits_finished_and_error(qapp):
    results, errors = [], []

    async def ok():
        return 42

    async def bad():
        raise RuntimeError("boom")

    tasks = []
    for coro in (ok, bad):
        t = ApiTask(coro)
        t.signals.finished.connect(results.append)
        t.signals.error.connect(errors.append)
        tasks.append(t)  # 持有引用，与 Controller 行为一致
        QThreadPool.globalInstance().start(t)
    assert QThreadPool.globalInstance().waitForDone(5000)
    qapp.processEvents()
    assert results == [42] and errors == ["boom"]
