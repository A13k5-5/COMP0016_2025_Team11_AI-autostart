import pystray
from PIL import Image
import os
from pathlib import Path

from multiprocessing import Process

# from src.gui.actions import update_app_data
# from src.systemTrayDesktopApp.runtimeSignals import request_recognizer_stop
from src.subprocesses.run_gesture_recogniser import run_gesture_recogniser
# from src.subprocesses.runGUI import run_gui

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

class SystemTrayApp:
    def __init__(self):
        self._recognizer_process: Process | None = None
        self._gui_process: Process | None = None
        self._gui_process: Process | None = None


    def _launch_recognizer_once(self) -> None:
        """Launch recognizer process only when it is not already running."""
        if self._recognizer_process is not None and self._recognizer_process.is_alive():
            print("Gesture monitoring is already running.")
            return

        self._recognizer_process = Process(target=run_gesture_recogniser, daemon=True)
        self._recognizer_process.start()

    def exit_app(self, icon, item):
        icon.stop()

    def gesture_monitoring(self, icon, item):
        self._launch_recognizer_once()

    # def stop_gesture_monitoring(self, icon, item):
    #     request_recognizer_stop()
    #     if self._recognizer_process is not None and self._recognizer_process.is_alive():
    #         _recognizer_process = None

    # def mapping_window(self, icon, item):
    #     if self._gui_process is not None and self._gui_process.is_alive():
    #         print("Settings window is already open.")
    #         return
    #     self._gui_process = Process(target=run_gui, daemon=False)
    #     self._gui_process.start()

    def main(self) -> None:
        """
        Start the system tray icon application.
        """
        # try:
        #     update_app_data()
        # except Exception as exc:
        #     print(f"Warning: failed to refresh app list: {exc}")

        image = Image.open(Path(__file__).parent / "icon.png")

        menu = pystray.Menu(
            pystray.MenuItem("Start gesture monitoring", self.gesture_monitoring),
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

        icon.run()


if __name__ == "__main__":
    app = SystemTrayApp()
    app.main()