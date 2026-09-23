"""主窗口：工具栏 + 双 Tab + 结果画布 + 历史抽屉 + 状态栏 + 非阻塞错误提示条。"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from nova_canvas.desktop.controller import AppController
from nova_canvas.schemas.history import HistoryRecord
from nova_canvas.schemas.image import ImageResponse, ModelName

from .edit_tab import EditTab
from .generate_tab import GenerateTab
from .history_panel import HistoryPanel
from .image_canvas import ImageCanvas
from .settings_dialog import SettingsDialog


class SegmentedTabs(QWidget):
    """独立 QTabBar（macOS 原生分段样式）+ QStackedWidget，没有 QTabWidget 的内容外框。"""

    def __init__(self) -> None:
        super().__init__()
        self.bar = QTabBar()
        self.bar.setExpanding(False)
        self.bar.setDrawBase(False)
        self.stack = QStackedWidget()
        self.bar.currentChanged.connect(self.stack.setCurrentIndex)
        bar_row = QHBoxLayout()
        bar_row.addStretch()
        bar_row.addWidget(self.bar)
        bar_row.addStretch()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(bar_row)
        lay.addWidget(self.stack, 1)

    def addTab(self, widget: QWidget, title: str) -> None:
        self.stack.addWidget(widget)
        self.bar.addTab(title)

    def setCurrentWidget(self, widget: QWidget) -> None:
        self.bar.setCurrentIndex(self.stack.indexOf(widget))

    def count(self) -> int:
        return self.bar.count()

    def tabText(self, i: int) -> str:
        return self.bar.tabText(i)


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.ctl = controller
        self.setWindowTitle("NovaCanvas 图片工作台")
        self.resize(1280, 800)
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()
        self._wire()
        self._apply_defaults()
        self._refresh_history()
        self._update_configured()
        if not self.ctl.configured:
            QTimer.singleShot(200, self.open_settings)  # 启动即引导配置

    # ---- 构建 ---------------------------------------------------------------------

    def _build_toolbar(self) -> None:
        tb = QToolBar("主工具栏")
        tb.setMovable(False)
        self.addToolBar(tb)
        title = QLabel("  NovaCanvas 图片工作台  ")
        title.setStyleSheet("font-weight: bold; font-size: 14px")
        tb.addWidget(title)
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding,
                             spacer.sizePolicy().verticalPolicy())
        tb.addWidget(spacer)
        tb.addWidget(QLabel("模型: "))
        self.model_combo = QComboBox()
        for m in ModelName:
            self.model_combo.addItem(m.value.replace("sensenova-", ""), m.value)
        tb.addWidget(self.model_combo)
        tb.addSeparator()
        self.history_btn = QPushButton("历史记录")
        self.history_btn.setCheckable(True)
        tb.addWidget(self.history_btn)
        self.settings_btn = QPushButton("⚙ 设置")
        self.settings_btn.clicked.connect(self.open_settings)
        tb.addWidget(self.settings_btn)

    def _build_central(self) -> None:
        self.banner = QLabel()
        self.banner.setWordWrap(True)
        self.banner.setStyleSheet(
            "background: #fdecea; color: #b71c1c; padding: 6px; border: 1px solid #f5c6c2")
        self.banner.hide()

        self.tabs = SegmentedTabs()
        self.generate_tab = GenerateTab()
        self.edit_tab = EditTab()
        self.tabs.addTab(self.generate_tab, "文生图")
        self.tabs.addTab(self.edit_tab, "编辑")
        self.canvas = ImageCanvas()
        self.history = HistoryPanel()

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self.tabs)
        split.addWidget(self.canvas)
        split.addWidget(self.history)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setStretchFactor(2, 0)
        split.setSizes([420, 620, 240])
        # 工具栏"历史记录"按钮控制第三栏显隐
        self.history_btn.setChecked(True)
        self.history_btn.toggled.connect(self.history.setVisible)

        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.addWidget(self.banner)
        lay.addWidget(split, 1)
        self.setCentralWidget(root)

    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        self.status_lbl = QLabel("状态: 就绪")
        self.usage_lbl = QLabel("")
        self.online_lbl = QLabel("● 在线")
        self.online_lbl.setStyleSheet("color: #2e7d32")
        sb.addWidget(self.status_lbl, 1)
        sb.addPermanentWidget(self.usage_lbl)
        sb.addPermanentWidget(QLabel("  |  "))
        sb.addPermanentWidget(self.online_lbl)

    def _wire(self) -> None:
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self.generate_tab.submit.connect(self.ctl.submit_generate)
        self.edit_tab.submit.connect(self.ctl.submit_edit)
        self.canvas.use_as_edit_input.connect(self._use_as_edit_input)
        self.history.selected.connect(self._show_record)
        self.history.refresh_btn.clicked.connect(self._refresh_history)
        self.history.delete_requested.connect(lambda rid: self.ctl.delete_history(rid, True))
        self.ctl.task_started.connect(self._on_started)
        self.ctl.task_finished.connect(self._on_finished)
        self.ctl.task_failed.connect(self._on_failed)
        self.ctl.history_changed.connect(self._refresh_history)

    # ---- 配置 ---------------------------------------------------------------------

    def _apply_defaults(self) -> None:
        c = self.ctl.config
        idx = self.model_combo.findData(c.default_model)
        self.model_combo.setCurrentIndex(max(idx, 0))
        self._on_model_changed()
        common = dict(output_format=c.default_output_format,
                      response_format=c.default_response_format,
                      watermark=c.watermark, prompt_extend=c.prompt_extend)
        self.generate_tab.panel.apply_defaults(size=c.default_size, **common)
        self.edit_tab.panel.apply_defaults(size="auto", **common)

    def _on_model_changed(self) -> None:
        model = self.model_combo.currentData()
        self.generate_tab.set_model(model)
        self.edit_tab.set_model(model)

    def _update_configured(self) -> None:
        ok = self.ctl.configured
        self.tabs.setEnabled(ok)
        self.online_lbl.setText("● 在线" if ok else "● 未配置 API Key")
        self.online_lbl.setStyleSheet(f"color: {'#2e7d32' if ok else '#b71c1c'}")

    def open_settings(self) -> None:
        if SettingsDialog(self.ctl.config, self).exec():
            self._apply_defaults()
            self._update_configured()
            self._refresh_history()
            self._set_status("设置已保存")

    # ---- 任务状态 -----------------------------------------------------------------

    def _on_started(self, kind: str) -> None:
        self.banner.hide()
        self._set_status("生成中…" if kind == "generate" else "编辑中…")
        self.generate_tab.panel.set_busy(True)
        self.edit_tab.panel.set_busy(True)

    def _on_finished(self, result: ImageResponse) -> None:
        self._restore()
        self.canvas.set_image(self.ctl.read_image(result.file_path), result.file_path)
        self._set_status(f"完成  ·  {result.size}  ·  已保存 {result.file_path}")
        u = result.usage
        self.usage_lbl.setText(
            f"本次消耗 total_tokens: {u.total_tokens} "
            f"(in {u.input_tokens} / out {u.output_tokens})")

    def _on_failed(self, message: str) -> None:
        self._restore()
        self.banner.setText(f"✖ {message}")
        self.banner.show()
        self._set_status(message, error=True)

    def _restore(self) -> None:
        self.generate_tab.panel.set_busy(False)
        self.edit_tab.panel.set_busy(False)

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status_lbl.setText(f"状态: {text}")
        self.status_lbl.setStyleSheet("color: #b71c1c" if error else "")

    # ---- 画布 / 历史 ---------------------------------------------------------------

    def _use_as_edit_input(self, data: bytes) -> None:
        if data:
            self.edit_tab.set_main_image(data)
            self.tabs.setCurrentWidget(self.edit_tab)
            self.edit_tab.panel.focus_prompt()

    def _show_record(self, rec: HistoryRecord) -> None:
        try:
            self.canvas.set_image(self.ctl.read_image(rec.file_path), rec.file_path)
        except Exception as exc:  # noqa: BLE001
            self._on_failed(str(exc))
            return
        self.usage_lbl.setText(f"历史记录 total_tokens: {rec.usage.total_tokens}")
        self._set_status(f"查看历史  ·  {rec.model}  ·  {rec.size}")

    def _refresh_history(self) -> None:
        if self.ctl.configured or self.ctl.config.output_dir.exists():
            try:
                self.history.set_records(self.ctl.list_history())
            except Exception:  # noqa: BLE001 — 历史损坏不应阻塞主界面
                self.history.set_records([])
