"""结果画布：滚轮缩放、适应窗口、1:1；下载 / 复制 / 作为编辑输入。"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _View(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class ImageCanvas(QWidget):
    use_as_edit_input = Signal(bytes)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bytes: bytes | None = None
        self._path: Path | None = None
        self._scene = QGraphicsScene(self)
        self._item: QGraphicsPixmapItem | None = None
        self.view = _View()
        self.view.setScene(self._scene)

        self.placeholder = QLabel("结果预览画布\n生成或编辑完成后在此显示")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #bbb; font-size: 15px")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.view, 1)
        self._scene.addWidget(self.placeholder)

        bar = QHBoxLayout()
        self.fit_btn = QPushButton("适应窗口")
        self.actual_btn = QPushButton("1:1")
        self.download_btn = QPushButton("下载")
        self.copy_btn = QPushButton("复制")
        self.edit_btn = QPushButton("作为编辑输入")
        self.fit_btn.clicked.connect(self.fit)
        self.actual_btn.clicked.connect(self.actual_size)
        self.download_btn.clicked.connect(self._download)
        self.copy_btn.clicked.connect(self._copy)
        self.edit_btn.clicked.connect(lambda: self.use_as_edit_input.emit(self._bytes))
        for b in (self.fit_btn, self.actual_btn):
            bar.addWidget(b)
        bar.addStretch()
        for b in (self.download_btn, self.copy_btn, self.edit_btn):
            bar.addWidget(b)
        lay.addLayout(bar)
        self._set_has_image(False)

    def _set_has_image(self, has: bool) -> None:
        for b in (self.fit_btn, self.actual_btn, self.download_btn, self.copy_btn, self.edit_btn):
            b.setEnabled(has)

    def set_image(self, data: bytes, path: str | None = None) -> None:
        pix = QPixmap()
        if not pix.loadFromData(data):
            return
        self._bytes, self._path = data, Path(path) if path else None
        self._scene.clear()
        self._item = self._scene.addPixmap(pix)
        self._scene.setSceneRect(self._item.boundingRect())
        self._set_has_image(True)
        self.fit()

    def fit(self) -> None:
        if self._item:
            self.view.fitInView(self._item, Qt.AspectRatioMode.KeepAspectRatio)

    def actual_size(self) -> None:
        self.view.resetTransform()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._item:
            self.fit()

    def _download(self) -> None:
        if not self._bytes:
            return
        default = self._path.name if self._path else "result.png"
        target, _ = QFileDialog.getSaveFileName(
            self, "另存为", default, "Images (*.png *.jpg *.jpeg *.webp)")
        if target:
            Path(target).write_bytes(self._bytes)

    def _copy(self) -> None:
        if self._item:
            QApplication.clipboard().setPixmap(self._item.pixmap())
