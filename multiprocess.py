# nuitka-project: --mode=standalone
from multiprocessing import Process
from PIL import Image
from pathlib import Path

import pystray

class SystemTrayApp:
    def __init__(self):
        self._recognizer_process: Process | None = None
        self._gui_process: Process | None = None
        self._gui_process: Process | None = None

    def do_something(self):
        print("Doing something in a separate process: 1.")

    def process1(self):
        process1 = Process(target=self.do_something)
        process1.start()

    def do_something2(self):
        print("Doing something else in a separate process: 2.")

    def process2(self):
        process2 = Process(target=self.do_something2)
        process2.start()

    def exit_app(self, icon, item):
        icon.stop()

    def main(self) -> None:
        """
        Start the system tray icon application.
        """
        image = Image.open(Path(__file__).parent / "icon.png")

        menu = pystray.Menu(
            pystray.MenuItem("Do something 1", self.process1),
            pystray.MenuItem("Do something 2", self.process2),
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

# def do_something():
#     print("Doing something in a separate process: 1.")
#
# def do_something2():
#     print("Doing something in a separate process: 2.")
#
# if __name__ == "__main__":
#     process1 = multiprocessing.Process(target=do_something)
#     process2 = multiprocessing.Process(target=do_something2)
#
#     process1.start()
#     process2.start()
#
#     print("Doing something in the main process.")