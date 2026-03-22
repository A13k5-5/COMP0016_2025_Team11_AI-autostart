# nuitka-project: --mode=standalone
from threading import Thread
from PIL import Image
from pathlib import Path

import pystray

from src.controller.controller import GestureController


class SystemTrayApp:
    def __init__(self):
        self._controller: GestureController = GestureController()
        self._recogniser_thread: Thread = Thread(target=self._controller.run)

    def run_controller_in_thread(self):
        if self._recogniser_thread.is_alive():
            return
        self._recogniser_thread.start()

    def exit_app(self, icon, item):
        icon.stop()

    def main(self) -> None:
        """
        Start the system tray icon application.
        """
        image = Image.open(Path(__file__).parent / "icon.png")

        menu = pystray.Menu(
            # pystray.MenuItem("Do something 1", self.process1),
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
