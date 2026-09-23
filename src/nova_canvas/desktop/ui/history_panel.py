"""历史记录抽屉：卡片列表（缩略图在上、文字在下、自动换行），一律读本地文件。"""
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nova_canvas.schemas.history import HistoryRecord

from .thin_scroll_area import ThinScrollArea

THUMB_SIDE = 180


def _thumb(path: str, side: int = THUMB_SIDE) -> QPixmap:
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid():
        size.scale(side, side, Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(size)  # 解码时缩放，避免加载 4K 原图
    img = reader.read()
    return QPixmap.fromImage(img) if not img.isNull() else QPixmap()


class HistoryCard(QFrame):
    clicked = Signal(object)  # HistoryRecord

    def __init__(self, record: HistoryRecord) -> None:
        super().__init__()
        self.record = record
        self.setObjectName("historyCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSelected(False)

        thumb = QLabel()
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setPixmap(_thumb(record.file_path))
        thumb.setMinimumHeight(60)

        when = datetime.fromtimestamp(record.created).strftime("%m-%d %H:%M")
        kind = "生成" if record.kind == "generate" else "编辑"
        meta = QLabel(f"[{kind}] {when}  ·  {record.size}")
        meta.setStyleSheet("color: #9a9a9a; font-size: 11px; background: transparent")
        prompt = QLabel(record.prompt)
        prompt.setWordWrap(True)
        prompt.setStyleSheet("background: transparent")
        prompt.setMaximumHeight(60)  # 约 3 行，超出截断
        self.setToolTip(f"{record.prompt}\n{record.model} · tokens={record.usage.total_tokens}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)
        lay.addWidget(thumb)
        lay.addWidget(meta)
        lay.addWidget(prompt)

    def setSelected(self, on: bool) -> None:
        border = "#3b82f6" if on else "transparent"
        self.setStyleSheet(
            f"QFrame#historyCard {{ background: rgba(255,255,255,0.06); border-radius: 8px;"
            f" border: 2px solid {border}; }}"
        )

    def mousePressEvent(self, _e) -> None:
        self.clicked.emit(self.record)


class HistoryPanel(QWidget):
    selected = Signal(object)        # HistoryRecord
    delete_requested = Signal(str)   # record_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: list[HistoryCard] = []
        self._current: HistoryCard | None = None

        self._container = QWidget()
        self._list = QVBoxLayout(self._container)
        self._list.setContentsMargins(6, 6, 12, 6)  # 右侧给覆盖层滚动条留位
        self._list.setSpacing(8)
        self._list.addStretch()

        scroll = ThinScrollArea()  # 悬浮显示的细滚动条，卡片宽度跟随视口
        scroll.setWidget(self._container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        box = QGroupBox("历史记录")  # 与"参数面板 / 输入图片"一致的卡片边框
        box_lay = QVBoxLayout(box)
        box_lay.setContentsMargins(4, 4, 4, 4)
        box_lay.addWidget(scroll)

        self.refresh_btn = QPushButton("刷新")
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete)
        btns = QHBoxLayout()  # 与画布按钮行同层级、同高度，保证水平对齐
        btns.addStretch()
        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.delete_btn)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(box, 1)
        lay.addLayout(btns)
        self.setMinimumWidth(THUMB_SIDE + 60)

    def set_records(self, records: list[HistoryRecord]) -> None:
        for c in self._cards:
            self._list.removeWidget(c)
            c.deleteLater()
        self._cards.clear()
        self._current = None
        self.delete_btn.setEnabled(False)
        for i, r in enumerate(records):
            card = HistoryCard(r)
            card.clicked.connect(self._on_card_clicked)
            self._list.insertWidget(i, card)
            self._cards.append(card)

    def _on_card_clicked(self, rec: HistoryRecord) -> None:
        for c in self._cards:
            c.setSelected(c.record.id == rec.id)
            if c.record.id == rec.id:
                self._current = c
        self.delete_btn.setEnabled(True)
        self.selected.emit(rec)

    def _delete(self) -> None:
        if self._current:
            self.delete_requested.emit(self._current.record.id)
