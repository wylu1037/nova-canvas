"""生成 / 编辑共用参数面板：prompt、size（预设 + 自定义实时校验）、格式、水印、动作按钮。"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nova_canvas.schemas.image import OutputFormat, ResponseFormat
from nova_canvas.utils.image_utils import SIZE_PRESETS, validate_size

CUSTOM = "自定义…"


class ParamPanel(QGroupBox):
    submitted = Signal()
    validity_changed = Signal(bool)

    def __init__(self, mode: str, parent: QWidget | None = None) -> None:
        super().__init__("参数面板", parent)
        self._mode = mode  # "generate" | "edit"
        self._external_ok = mode == "generate"  # 编辑模式需外部告知"已有主图"
        self._busy = False
        self._build()
        self._revalidate()

    # ---- 构建 -------------------------------------------------------------------

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        label = "提示词 (prompt)" if self._mode == "generate" else "编辑指令 (prompt)"
        lay.addWidget(QLabel(label))
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(
            "描述你想生成的画面…" if self._mode == "generate" else "描述要如何修改主图…"
        )
        self.prompt.setMinimumHeight(110)
        self.prompt.textChanged.connect(self._revalidate)
        lay.addWidget(self.prompt)

        self.prompt_extend = QCheckBox("自动润色 (prompt_extend)")
        self.prompt_extend.setChecked(True)
        lay.addWidget(self.prompt_extend)

        form = QFormLayout()
        self.size = QComboBox()
        self.size.addItem("auto (适配主图)" if self._mode == "edit" else "auto", "auto")
        for s, meta in SIZE_PRESETS.items():
            self.size.addItem(f"{s} · {meta['ratio']} · {meta['tier']}", s)
        self.size.addItem(CUSTOM, CUSTOM)
        self.size.currentIndexChanged.connect(self._on_size_changed)
        form.addRow("尺寸 (size)", self.size)

        self.custom_row = QWidget()
        h = QHBoxLayout(self.custom_row)
        h.setContentsMargins(0, 0, 0, 0)
        self.w_edit, self.h_edit = QLineEdit(), QLineEdit()
        for e, ph in ((self.w_edit, "W"), (self.h_edit, "H")):
            e.setPlaceholderText(ph)
            e.setMaxLength(4)
            e.textChanged.connect(self._revalidate)
        h.addWidget(self.w_edit)
        h.addWidget(QLabel("x"))
        h.addWidget(self.h_edit)
        self.custom_hint = QLabel("32 的倍数，512~4096，比例 ≤ 3:1")
        self.custom_hint.setStyleSheet("color: gray; font-size: 11px")
        form.addRow("自定义", self.custom_row)
        form.addRow("", self.custom_hint)
        self.custom_row.hide()
        self.custom_hint.hide()

        self.output_format = QComboBox()
        self.output_format.addItems([f.value for f in OutputFormat])
        form.addRow("输出格式", self.output_format)
        self.response_format = QComboBox()
        self.response_format.addItems([f.value for f in ResponseFormat])
        form.addRow("返回方式", self.response_format)
        lay.addLayout(form)

        self.watermark = QCheckBox("添加水印 (watermark)")
        lay.addWidget(self.watermark)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 不确定进度 → 旋转/滚动样式
        self.progress.hide()
        lay.addWidget(self.progress)

        self.button = QPushButton("生成" if self._mode == "generate" else "编辑")
        self.button.setMinimumHeight(36)
        self.button.clicked.connect(self.submitted.emit)
        lay.addWidget(self.button)
        lay.addStretch()

    # ---- 校验 -------------------------------------------------------------------

    def _on_size_changed(self) -> None:
        custom = self.size.currentData() == CUSTOM
        self.custom_row.setVisible(custom)
        self.custom_hint.setVisible(custom)
        self._revalidate()

    def size_value(self) -> str:
        if self.size.currentData() == CUSTOM:
            return f"{self.w_edit.text().strip()}x{self.h_edit.text().strip()}"
        return self.size.currentData()

    def _size_error(self) -> str | None:
        try:
            validate_size(self.size_value())
        except ValueError as exc:
            return str(exc)
        return None

    def _revalidate(self) -> None:
        err = self._size_error()
        red = "border: 1px solid #d33"
        for e in (self.w_edit, self.h_edit):
            e.setStyleSheet(red if err and self.size.currentData() == CUSTOM else "")
        self.custom_hint.setText(err or "32 的倍数，512~4096，比例 ≤ 3:1")
        self.custom_hint.setStyleSheet(f"color: {'#d33' if err else 'gray'}; font-size: 11px")
        ok = bool(self.prompt.toPlainText().strip()) and err is None and self._external_ok
        self.button.setEnabled(ok and not self._busy)
        self.validity_changed.emit(ok)

    def set_external_ok(self, ok: bool) -> None:
        self._external_ok = ok
        self._revalidate()

    # ---- 状态 / 取值 ---------------------------------------------------------------

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.progress.setVisible(busy)
        self.button.setText(
            ("生成中…" if self._mode == "generate" else "编辑中…") if busy
            else ("生成" if self._mode == "generate" else "编辑")
        )
        self._revalidate()

    def apply_defaults(self, *, size: str, output_format: str, response_format: str,
                       watermark: bool, prompt_extend: bool) -> None:
        idx = self.size.findData(size)
        self.size.setCurrentIndex(idx if idx >= 0 else 0)
        self.output_format.setCurrentText(output_format)
        self.response_format.setCurrentText(response_format)
        self.watermark.setChecked(watermark)
        self.prompt_extend.setChecked(prompt_extend)

    def params(self) -> dict:
        return {
            "prompt": self.prompt.toPlainText().strip(),
            "size": self.size_value(),
            "output_format": self.output_format.currentText(),
            "response_format": self.response_format.currentText(),
            "watermark": self.watermark.isChecked(),
            "prompt_extend": self.prompt_extend.isChecked(),
        }

    def focus_prompt(self) -> None:
        self.prompt.setFocus(Qt.FocusReason.OtherFocusReason)
