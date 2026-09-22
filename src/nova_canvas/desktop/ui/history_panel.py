"""历史记录抽屉：缩略图列表，一律读本地文件。"""
from datetime import datetime

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nova_canvas.schemas.history import HistoryRecord


def _thumb(path: str, side: int = 96) -> QIcon:
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid():
        size.scale(side, side, Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(size)  # 解码时缩放，避免加载 4K 原图
    img = reader.read()
    return QIcon(QPixmap.fromImage(img)) if not img.isNull() else QIcon()


class HistoryPanel(QWidget):
    selected = Signal(object)        # HistoryRecord
    delete_requested = Signal(str)   # record_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.list = QListWidget()
        self.list.setIconSize(QSize(96, 96))
        self.list.setSpacing(4)
        self.list.itemClicked.connect(
            lambda it: self.selected.emit(it.data(Qt.ItemDataRole.UserRole)))
        self.refresh_btn = QPushButton("刷新")
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._delete)
        btns = QHBoxLayout()
        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.delete_btn)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addWidget(self.list, 1)
        lay.addLayout(btns)

    def set_records(self, records: list[HistoryRecord]) -> None:
        self.list.clear()
        for r in records:
            when = datetime.fromtimestamp(r.created).strftime("%m-%d %H:%M")
            kind = "生成" if r.kind == "generate" else "编辑"
            text = f"[{kind}] {when}\n{r.prompt[:40]}{'…' if len(r.prompt) > 40 else ''}"
            item = QListWidgetItem(_thumb(r.file_path), text)
            item.setData(Qt.ItemDataRole.UserRole, r)
            item.setToolTip(f"{r.prompt}\n{r.model} · {r.size} · tokens={r.usage.total_tokens}")
            self.list.addItem(item)

    def _delete(self) -> None:
        it = self.list.currentItem()
        if it:
            self.delete_requested.emit(it.data(Qt.ItemDataRole.UserRole).id)
