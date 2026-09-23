from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from nova_canvas.schemas.image import GenerateRequest

from .param_panel import ParamPanel


class GenerateTab(QWidget):
    submit = Signal(object)  # GenerateRequest

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.panel = ParamPanel("generate")
        self.panel.submitted.connect(self._on_submit)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.addWidget(self.panel)
        self._model = ""

    def set_model(self, model: str) -> None:
        self._model = model

    def _on_submit(self) -> None:
        self.submit.emit(GenerateRequest(model=self._model, **self.panel.params()))
