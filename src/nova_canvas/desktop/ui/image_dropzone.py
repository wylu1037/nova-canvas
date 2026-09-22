"""编辑页输入图：主图（拖拽 / 点击 / URL）+ 参考图列表（最多 4 张）。本地文件自动转 Data URL。"""
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nova_canvas.utils.image_utils import make_thumbnail, to_data_url

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"
MAX_REFS = 4


def _pix_from_bytes(data: bytes) -> QPixmap:
    pix = QPixmap()
    pix.loadFromData(make_thumbnail(data, 256))
    return pix


class _MainDrop(QLabel):
    """主编辑图区域：接受拖拽，点击打开文件对话框。"""

    file_dropped = Signal(str)
    clicked = Signal()

    def __init__(self) -> None:
        super().__init__("拖拽 / 点击上传主编辑图")
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(220, 160)
        self.setStyleSheet("border: 2px dashed #999; border-radius: 6px; color: #888")

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:
        for url in e.mimeData().urls():
            if url.isLocalFile():
                self.file_dropped.emit(url.toLocalFile())
                return

    def mousePressEvent(self, _e) -> None:
        self.clicked.emit()


class ImageDropZone(QGroupBox):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("输入图片", parent)
        self._main: str | None = None  # data URL 或 http URL
        self._refs: list[str] = []
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("主编辑图 (必填)"))
        self.main_drop = _MainDrop()
        self.main_drop.file_dropped.connect(self._load_main_file)
        self.main_drop.clicked.connect(self._pick_main)
        lay.addWidget(self.main_drop)

        url_row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("或粘贴公网图片 URL (http/https)")
        use_url = QPushButton("使用 URL")
        use_url.clicked.connect(self._use_url)
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(use_url)
        lay.addLayout(url_row)

        self.size_hint = QLabel("")
        self.size_hint.setStyleSheet("color: gray; font-size: 11px")
        lay.addWidget(self.size_hint)

        lay.addWidget(QLabel(f"参考图 (可选, 最多 {MAX_REFS} 张)"))
        self.ref_list = QListWidget()
        self.ref_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.ref_list.setIconSize(QSize(72, 72))
        self.ref_list.setFixedHeight(100)
        self.ref_list.setMovement(QListWidget.Movement.Static)
        lay.addWidget(self.ref_list)
        ref_btns = QHBoxLayout()
        self.add_ref = QPushButton("＋ 添加参考图")
        self.del_ref = QPushButton("移除选中")
        self.add_ref.clicked.connect(self._pick_refs)
        self.del_ref.clicked.connect(self._remove_ref)
        ref_btns.addWidget(self.add_ref)
        ref_btns.addWidget(self.del_ref)
        lay.addLayout(ref_btns)
        tip = QLabel("支持: 本地文件 / 公网 URL。大图 Base64 会显著增加 input_tokens。")
        tip.setStyleSheet("color: gray; font-size: 11px")
        tip.setWordWrap(True)
        lay.addWidget(tip)

    # ---- 主图 -------------------------------------------------------------------

    def _pick_main(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择主编辑图", "", IMAGE_FILTER)
        if path:
            self._load_main_file(path)

    def _load_main_file(self, path: str) -> None:
        try:
            self.set_main_image(Path(path).read_bytes())
        except (OSError, ValueError):
            self.main_drop.setText("无法读取该图片")

    def set_main_image(self, data: bytes) -> None:
        self._main = to_data_url(data)
        self.main_drop.setPixmap(_pix_from_bytes(data).scaled(
            self.main_drop.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.size_hint.setText(f"主图 Base64 约 {len(self._main) / 1024:.0f} KB")
        self.url_edit.clear()
        self.changed.emit()

    def _use_url(self) -> None:
        url = self.url_edit.text().strip()
        if not url.startswith(("http://", "https://")):
            self.size_hint.setText("URL 必须以 http:// 或 https:// 开头")
            return
        self._main = url
        self.main_drop.setPixmap(QPixmap())
        self.main_drop.setText("主图: 公网 URL")
        self.size_hint.setText(url[:60] + ("…" if len(url) > 60 else ""))
        self.changed.emit()

    # ---- 参考图 ------------------------------------------------------------------

    def _pick_refs(self) -> None:
        remaining = MAX_REFS - len(self._refs)
        if remaining <= 0:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "选择参考图", "", IMAGE_FILTER)
        for p in paths[:remaining]:
            try:
                data = Path(p).read_bytes()
                item = QListWidgetItem(QIcon(_pix_from_bytes(data)), Path(p).name)
                self._refs.append(to_data_url(data))
                self.ref_list.addItem(item)
            except (OSError, ValueError):
                continue
        self.add_ref.setEnabled(len(self._refs) < MAX_REFS)
        self.changed.emit()

    def _remove_ref(self) -> None:
        row = self.ref_list.currentRow()
        if row >= 0:
            self.ref_list.takeItem(row)
            self._refs.pop(row)
            self.add_ref.setEnabled(True)
            self.changed.emit()

    # ---- 取值 --------------------------------------------------------------------

    @property
    def has_main(self) -> bool:
        return self._main is not None

    def images(self) -> list[str]:
        return ([self._main] if self._main else []) + self._refs
