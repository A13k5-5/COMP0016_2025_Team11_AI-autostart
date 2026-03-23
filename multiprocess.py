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

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from src.controller.controller import GestureController
from src.gui.gestureMappingWindow import MappingWindow


class SystemTrayApp:
    def __init__(self):
        self._controller: GestureController = GestureController()
        self._recogniser_thread: Thread | None = None
        self.app: QApplication | None = None

    def run_controller_in_thread(self):
        if self._recogniser_thread and self._recogniser_thread.is_alive():
            return
        self._recogniser_thread = Thread(target=self._controller.run)
        self._recogniser_thread.start()

    def exit_app(self):
        self._controller.stop()
        self.app.quit()

    def run(self) -> None:
        """
        Start the system tray icon application.
        """
        self.app = QApplication([])
        self.app.setQuitOnLastWindowClosed(False)
        icon = QIcon("icon.png")

        # Create the tray
        tray = QSystemTrayIcon()
        tray.setIcon(icon)
        tray.setVisible(True)

        # Create the menu
        menu = QMenu()

        action1 = QAction("Start recognition")
        action1.triggered.connect(self.run_controller_in_thread)
        menu.addAction(action1)

        action2 = QAction("Stop recognition")
        action2.triggered.connect(self._controller.stop)
        menu.addAction(action2)

        mapping_window = MappingWindow(self._controller)
        action3 = QAction("Open mapping window")
        action3.triggered.connect(mapping_window.show)
        menu.addAction(action3)

        action4 = QAction("Exit")
        action4.triggered.connect(self.exit_app)
        menu.addAction(action4)

        tray.setContextMenu(menu)
        self.app.exec()


if __name__ == "__main__":
    app = SystemTrayApp()
    app.run()
