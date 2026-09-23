from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from nova_canvas.schemas.image import EditRequest

from .image_dropzone import ImageDropZone
from .param_panel import ParamPanel


class EditTab(QWidget):
    submit = Signal(object)  # EditRequest

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.dropzone = ImageDropZone()
        self.panel = ParamPanel("edit")
        self.dropzone.changed.connect(lambda: self.panel.set_external_ok(self.dropzone.has_main))
        self.panel.submitted.connect(self._on_submit)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)
        lay.addWidget(self.dropzone, 1)
        lay.addWidget(self.panel, 1)
        self._model = ""

    def set_model(self, model: str) -> None:
        self._model = model

    def set_main_image(self, data: bytes) -> None:
        self.dropzone.set_main_image(data)

    def _on_submit(self) -> None:
        self.submit.emit(
            EditRequest(model=self._model, images=self.dropzone.images(), **self.panel.params())
        )
