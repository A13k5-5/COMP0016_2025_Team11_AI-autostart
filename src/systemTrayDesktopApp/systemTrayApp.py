import pystray
from PIL import Image
import sys
import os

from PySide6.QtWidgets import QApplication

from src.controller.controller import GestureController
from src.gui.actions import update_app_data
from src.gui.gestureMappingWindow import MappingWindow
from src.systemTrayDesktopApp.runtimeSignals import request_recognizer_stop

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

def exit_app(icon, item):
    icon.stop()

def gesture_monitoring(icon, item):
    controller: GestureController = GestureController()
    controller.run()

def stop_gesture_monitoring(icon, item):
    global _recognizer_process
    request_recognizer_stop()
    if _recognizer_process is not None and _recognizer_process.poll() is not None:
        _recognizer_process = None

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
        update_app_data()
    except Exception as exc:
        print(f"Warning: failed to refresh app list: {exc}")
    
    image = Image.open(os.path.join(BASE_DIR, "icon.png"))

    menu = pystray.Menu(
        pystray.MenuItem("Start gesture monitoring", gesture_monitoring),
        pystray.MenuItem("Stop gesture monitoring", stop_gesture_monitoring),
        pystray.MenuItem("Open settings", mapping_window),
        pystray.MenuItem("Exit", exit_app)
    )

    icon = pystray.Icon(
        name="AI-Autostart",
        icon=image,
        title="AI Autostart",
        menu=menu
    )

    icon.run()


if __name__ == "__main__":
    main()