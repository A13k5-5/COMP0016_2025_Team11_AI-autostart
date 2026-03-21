import pystray
from PIL import Image
import sys
import os

from PySide6.QtWidgets import QApplication

from src.controller.controller import GestureController
from src.gui import actions
from src.gui.gestureMappingWindow import MappingWindow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

class App:
    def __init__(self):
        self.controller: GestureController = GestureController()
        self.system_tray_icon  = self._build_system_tray_icon()

    def run(self):
        self.system_tray_icon.run()

    def exit_app(self):
        self.system_tray_icon.stop()

    def start_gesture_monitoring(self):
        self.controller.run()

    def _build_system_tray_icon(self):
        image = Image.open(os.path.join(BASE_DIR, "icon.png"))

        menu = pystray.Menu(
            pystray.MenuItem("Start gesture monitoring", self.start_gesture_monitoring),
            # pystray.MenuItem("Stop gesture monitoring", self.stop_gesture_monitoring),
            # pystray.MenuItem("Open settings", self.mapping_window),
            pystray.MenuItem("Exit", self.exit_app)
        )

        icon = pystray.Icon(
            name="AI-Autostart",
            icon=image,
            title="AI Autostart",
            menu=menu
        )

        return icon


def mapping_window(icon, item):
    app = QApplication(sys.argv)
    w = MappingWindow()
    w.show()
    app.exec()

def main() -> None:
    """
    Start the system tray icon application.
    """
    try:
        actions.update_app_data()
    except Exception as exc:
        print(f"Warning: failed to refresh app list: {exc}")


if __name__ == "__main__":
    app = App()
    app.run()
