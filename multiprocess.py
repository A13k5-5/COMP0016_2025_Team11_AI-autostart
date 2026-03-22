# nuitka-project: --mode=standalone

# for pyside6
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-qt-plugins=qml

# recognizer file for mediapipe
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/video_recogniser/gesture_recogniser/gesture_recognizer.task=src/video_recogniser/gesture_recogniser/gesture_recognizer.task

# icons
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/systemTrayDesktopApp/icon.png=src/systemTrayDesktopApp/icon.png
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/icon.png=icon.png

from threading import Thread
from PIL import Image
from pathlib import Path

import pystray

from src.controller.controller import GestureController


class SystemTrayApp:
    def __init__(self):
        self._controller: GestureController = GestureController()
        self._recogniser_thread: Thread | None = None

    def run_controller_in_thread(self):
        if self._recogniser_thread and self._recogniser_thread.is_alive():
            return
        self._recogniser_thread = Thread(target=self._controller.run)
        self._recogniser_thread.start()

    def exit_app(self, icon, item):
        self._controller.stop()
        icon.stop()

    def main(self) -> None:
        """
        Start the system tray icon application.
        """
        image = Image.open(Path(__file__).parent / "icon.png")

        menu = pystray.Menu(
            pystray.MenuItem("Start recognition", self.run_controller_in_thread),
            pystray.MenuItem("Stop recognition", self._controller.stop),
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
