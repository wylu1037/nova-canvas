"""桌面入口：启动 QApplication。"""
import sys

from PySide6.QtWidgets import QApplication

from nova_canvas.core.logging import setup_logging
from nova_canvas.desktop.config import ConfigStore
from nova_canvas.desktop.controller import AppController
from nova_canvas.desktop.ui.main_window import MainWindow


def run() -> int:
    setup_logging("INFO")
    app = QApplication(sys.argv)
    app.setApplicationName("NovaCanvas")
    app.setOrganizationName("NovaCanvas")
    controller = AppController(ConfigStore())
    win = MainWindow(controller)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
