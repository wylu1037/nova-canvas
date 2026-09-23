"""设置对话框：API Key（会话/持久化）、Base URL、默认参数、落盘目录。"""
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QWidget,
)

from nova_canvas.desktop.config import ConfigStore
from nova_canvas.schemas.image import ModelName, OutputFormat, ResponseFormat
from nova_canvas.utils.image_utils import SIZE_PRESETS


class SettingsDialog(QDialog):
    def __init__(self, config: ConfigStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(560)
        self._cfg = config
        form = QFormLayout(self)
        # macOS 默认 FieldsStayAtSizeHint，输入框不随窗口拉伸
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        key_row = QHBoxLayout()
        self.key = QLineEdit(config.api_key)
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("sk-…")
        show = QPushButton("显示")
        show.setCheckable(True)
        show.toggled.connect(lambda on: self.key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        key_row.addWidget(self.key, 1)
        key_row.addWidget(show)
        form.addRow("API Key", key_row)
        if config.api_key_from_env:
            note = QLabel("已从环境变量 SENSENOVA_API_KEY 读取，环境变量优先级最高。")
            note.setStyleSheet("color: gray; font-size: 11px")
            form.addRow("", note)
            self.key.setEnabled(False)

        self.base_url = QLineEdit(config.base_url)
        form.addRow("Base URL", self.base_url)

        save_row = QHBoxLayout()
        self.session_only = QRadioButton("仅本次会话")
        self.persist = QRadioButton("持久化")
        (self.persist if config.api_key_persisted else self.session_only).setChecked(True)
        save_row.addWidget(self.session_only)
        save_row.addWidget(self.persist)
        form.addRow("保存方式", save_row)
        warn = QLabel("⚠ 持久化会以明文写入本机配置（QSettings），请确保设备安全。")
        warn.setStyleSheet("color: #b58900; font-size: 11px")
        form.addRow("", warn)  # 不换行；对话框最小宽度足以单行显示

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        form.addRow(line)

        self.model = QComboBox()
        self.model.addItems([m.value for m in ModelName])
        self.model.setCurrentText(config.default_model)
        form.addRow("默认模型", self.model)
        self.size = QComboBox()
        self.size.addItems(["auto", *SIZE_PRESETS])
        self.size.setCurrentText(config.default_size)
        form.addRow("默认尺寸", self.size)
        fmt_row = QHBoxLayout()
        self.output_format = QComboBox()
        self.output_format.addItems([f.value for f in OutputFormat])
        self.output_format.setCurrentText(config.default_output_format)
        self.response_format = QComboBox()
        self.response_format.addItems([f.value for f in ResponseFormat])
        self.response_format.setCurrentText(config.default_response_format)
        fmt_row.addWidget(QLabel("输出"))
        fmt_row.addWidget(self.output_format)
        fmt_row.addWidget(QLabel("返回"))
        fmt_row.addWidget(self.response_format)
        form.addRow("默认格式", fmt_row)
        self.watermark = QCheckBox("默认添加水印")
        self.watermark.setChecked(config.watermark)
        form.addRow("", self.watermark)

        dir_row = QHBoxLayout()
        self.output_dir = QLineEdit(str(config.output_dir))
        browse = QPushButton("浏览")
        browse.clicked.connect(self._browse)
        dir_row.addWidget(self.output_dir, 1)
        dir_row.addWidget(browse)
        form.addRow("落盘目录", dir_row)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "选择落盘目录", self.output_dir.text())
        if d:
            self.output_dir.setText(d)

    def _save(self) -> None:
        c = self._cfg
        if not c.api_key_from_env:
            c.set_api_key(self.key.text(), persist=self.persist.isChecked())
        c.base_url = self.base_url.text().strip() or "https://token.sensenova.cn/v1"
        c.default_model = self.model.currentText()
        c.default_size = self.size.currentText()
        c.default_output_format = self.output_format.currentText()
        c.default_response_format = self.response_format.currentText()
        c.watermark = self.watermark.isChecked()
        c.output_dir = self.output_dir.text().strip() or "./output"
        self.accept()
