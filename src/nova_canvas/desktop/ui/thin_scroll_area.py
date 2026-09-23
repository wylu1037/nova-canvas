"""shadcn/ui ScrollArea 风格的细滚动条：悬浮淡入、移开淡出、可拖拽，覆盖在内容之上不占布局宽度。"""
from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import QGraphicsOpacityEffect, QScrollArea, QWidget

TRACK_W = 10      # 覆盖层宽度（含留白，便于命中）
THUMB_W = 5       # thumb 实际宽度
MIN_THUMB = 24
HIDE_DELAY_MS = 600


class _OverlayThumb(QWidget):
    """竖向 thumb 覆盖层，与 QScrollBar 的 range/value 同步。"""

    def __init__(self, area: QScrollArea) -> None:
        super().__init__(area)
        self._area = area
        self._bar = area.verticalScrollBar()
        self._drag_start_y: int | None = None
        self._drag_start_val = 0
        self._hover = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b"opacity", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(lambda: self._fade(0.0))

        self._bar.rangeChanged.connect(lambda *_: self.update())
        self._bar.valueChanged.connect(lambda *_: self.update())

    # ---- 显隐 ------------------------------------------------------------------

    def _fade(self, to: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._fx.opacity())
        self._anim.setEndValue(to)
        self._anim.start()

    def show_temporarily(self) -> None:
        if self._bar.maximum() <= 0:
            return
        self._hide_timer.stop()
        self._fade(1.0)
        if not self._hover and self._drag_start_y is None:
            self._hide_timer.start(HIDE_DELAY_MS)

    def set_hover(self, on: bool) -> None:
        self._hover = on
        if on:
            self.show_temporarily()
        elif self._drag_start_y is None:
            self._hide_timer.start(HIDE_DELAY_MS)

    # ---- 几何 ------------------------------------------------------------------

    def _thumb_rect(self) -> QRect:
        total = self._bar.maximum() + self._bar.pageStep()
        if total <= 0 or self._bar.maximum() <= 0:
            return QRect()
        h = self.height()
        thumb_h = max(MIN_THUMB, int(h * self._bar.pageStep() / total))
        travel = h - thumb_h
        y = int(travel * self._bar.value() / self._bar.maximum()) if travel > 0 else 0
        x = (self.width() - THUMB_W) // 2
        return QRect(x, y, THUMB_W, thumb_h)

    def paintEvent(self, _e) -> None:
        r = self._thumb_rect()
        if r.isNull():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        alpha = 150 if (self._hover or self._drag_start_y is not None) else 110
        p.setBrush(QColor(255, 255, 255, alpha))
        p.drawRoundedRect(r, THUMB_W / 2, THUMB_W / 2)

    # ---- 交互 ------------------------------------------------------------------

    def mousePressEvent(self, e: QMouseEvent) -> None:
        r = self._thumb_rect()
        if r.isNull():
            return
        y = int(e.position().y())
        if not r.contains(int(e.position().x()), y):
            # 点击轨道：thumb 中心跳到点击处
            self._bar.setValue(self._value_for_y(y - r.height() // 2))
            r = self._thumb_rect()
        self._drag_start_y = y
        self._drag_start_val = self._bar.value()
        self.update()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag_start_y is None:
            return
        delta = int(e.position().y()) - self._drag_start_y
        travel = self.height() - self._thumb_rect().height()
        if travel > 0:
            self._bar.setValue(self._drag_start_val + int(delta * self._bar.maximum() / travel))

    def mouseReleaseEvent(self, _e) -> None:
        self._drag_start_y = None
        self.update()
        if not self._hover:
            self._hide_timer.start(HIDE_DELAY_MS)

    def _value_for_y(self, y: int) -> int:
        travel = self.height() - self._thumb_rect().height()
        return int(max(0, min(y, travel)) * self._bar.maximum() / travel) if travel > 0 else 0


class ThinScrollArea(QScrollArea):
    """隐藏原生滚动条（保留滚轮），用覆盖层细 thumb 代替。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self._thumb = _OverlayThumb(self)
        self._thumb.raise_()
        self.viewport().installEventFilter(self)
        self.verticalScrollBar().valueChanged.connect(lambda *_: self._thumb.show_temporarily())

    def _place_thumb(self) -> None:
        vp = self.viewport().geometry()
        self._thumb.setGeometry(vp.right() - TRACK_W + 1, vp.top(), TRACK_W, vp.height())
        self._thumb.raise_()

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._place_thumb()

    def showEvent(self, e) -> None:
        super().showEvent(e)
        self._place_thumb()

    def enterEvent(self, e) -> None:
        super().enterEvent(e)
        self._thumb.set_hover(True)

    def leaveEvent(self, e) -> None:
        super().leaveEvent(e)
        self._thumb.set_hover(False)

    def eventFilter(self, obj, e) -> bool:
        if obj is self.viewport() and e.type() == QEvent.Type.Wheel:
            self._thumb.show_temporarily()
        return super().eventFilter(obj, e)
