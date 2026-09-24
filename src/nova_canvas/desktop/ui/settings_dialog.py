"""设置对话框：API Key（会话/持久化）、Base URL、默认参数、落盘目录。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from nova_canvas.desktop.config import ConfigStore
from nova_canvas.schemas.image import ModelName, OutputFormat, ResponseFormat
from nova_canvas.utils.image_utils import SIZE_PRESETS

# 统一行距。macOS 样式默认按控件类型给出不等间距（按钮行 20、其它 10）；
# 且会把控件超出布局矩形的部分（最多 4pt）作为最小间距，取值需不小于它才能真正均匀。
ROW_SPACING = 8


def _add(target: QLayout, item: QWidget | QLayout, *args) -> None:
    """QLayout 对控件与子布局是两个方法，这里按类型分发。"""
    (target.addLayout if isinstance(item, QLayout) else target.addWidget)(item, *args)


class SettingsDialog(QDialog):
    def __init__(self, config: ConfigStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(560)
        self._cfg = config
        # 三列网格：标签 | 控件 | 行尾按钮。Base URL 行第三列留空，输入框右缘即与
        # API Key / 落盘目录行对齐。不用 QFormLayout 是因为 macOS 样式会按控件类型
        # 给出不等的行距，这里每行等高、行距统一（见 _add_row）。
        self._grid = QGridLayout(self)
        self._grid.setColumnStretch(1, 1)
        self._grid.setVerticalSpacing(ROW_SPACING)
        self._rows = 0

        self.key = QLineEdit(config.api_key)
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("sk-…")
        show = QPushButton("显示")
        show.setCheckable(True)
        show.toggled.connect(lambda on: self.key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        # 统一行高：取输入框与按钮中较高者（macOS 下按钮 32pt），各行控件在行内垂直居中
        self._row_h = max(self.key.sizeHint().height(), show.sizeHint().height())
        note = None
        if config.api_key_from_env:
            note = QLabel("已从环境变量 SENSENOVA_API_KEY 读取，环境变量优先级最高。")
            note.setStyleSheet("color: gray; font-size: 11px")
            self.key.setEnabled(False)
        self._add_row("API Key", self.key, trailing=show, note=note)

        self.base_url = QLineEdit(config.base_url)
        self._add_row("Base URL", self.base_url)

        save_row = QHBoxLayout()
        self.session_only = QRadioButton("仅本次会话")
        self.persist = QRadioButton("持久化")
        (self.persist if config.api_key_persisted else self.session_only).setChecked(True)
        save_row.addWidget(self.session_only)
        save_row.addWidget(self.persist)
        warn = QLabel("⚠ 持久化会以明文写入本机配置（QSettings），请确保设备安全。")
        warn.setStyleSheet("color: #b58900; font-size: 11px")
        self._add_row("保存方式", save_row, note=warn)  # 不换行；对话框最小宽度足以单行显示

        self.model = QComboBox()
        self.model.addItems([m.value for m in ModelName])
        self.model.setCurrentText(config.default_model)
        self._add_row("默认模型", self.model)
        self.size = QComboBox()
        self.size.addItems(["auto", *SIZE_PRESETS])
        self.size.setCurrentText(config.default_size)
        self._add_row("默认尺寸", self.size)
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
        self._add_row("默认格式", fmt_row)
        self.watermark = QCheckBox("默认添加水印")
        self.watermark.setChecked(config.watermark)
        self._add_row("", self.watermark)

        self.output_dir = QLineEdit(str(config.output_dir))
        browse = QPushButton("浏览")
        browse.clicked.connect(self._browse)
        self._add_row("落盘目录", self.output_dir, trailing=browse)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        self._grid.addWidget(btns, self._rows, 0, 1, 3)

    def _add_row(
        self,
        text: str,
        field: QWidget | QLayout,
        *,
        trailing: QWidget | None = None,
        note: QLabel | None = None,
    ) -> None:
        """追加一行：标签 | 控件 | 行尾按钮。

        标签固定为行高并顶对齐，控件在行内垂直居中；输入框横向铺满、其余控件靠左
        （同 QFormLayout 的 ExpandingFieldsGrow）；note 紧贴控件正下方，与控件同占一格。
        """
        g, r = self._grid, self._rows
        self._rows += 1
        label = QLabel(text)
        label.setFixedHeight(self._row_h)
        g.addWidget(label, r, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        fill = isinstance(field, QWidget) and bool(
            field.sizePolicy().expandingDirections() & Qt.Orientation.Horizontal)
        if note is not None:
            first = QHBoxLayout()
            first.addStrut(self._row_h)  # 首行撑满行高，note 紧贴其下
            _add(first, field)
            if not fill:
                first.addStretch()
            box = QVBoxLayout()
            box.setSpacing(0)  # 首行控件在行高内居中、下方已有空隙，note 直接贴上
            box.addLayout(first)
            box.addWidget(note)
            field, fill = box, True
        if fill:
            _add(g, field, r, 1)
        else:
            _add(g, field, r, 1, Qt.AlignmentFlag.AlignLeft)
        if trailing is not None:
            # macOS 按钮的 widget 矩形比样式布局矩形上下各多 4pt，直接顶对齐会整体偏高；
            # 改按 widget 矩形排版，有 note 时也能与首行控件居中对齐
            trailing.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)
            g.addWidget(trailing, r, 2, Qt.AlignmentFlag.AlignTop)

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
