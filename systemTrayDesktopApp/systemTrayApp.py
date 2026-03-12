import pystray
from PIL import Image
import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

def _launch_script(script_name: str) -> None:
    """Launch a project script in a separate process."""
    script_path = os.path.join(PROJECT_ROOT, script_name)
    subprocess.Popen([sys.executable, script_path], cwd=PROJECT_ROOT)

def exit_app(icon, item):
    icon.stop()

def gesture_monitoring(icon, item):
    _launch_script("main.py")

def mapping_window(icon, item):
    _launch_script("runGUI.py")

def main() -> None:
    """
    Start the system tray icon application.
    """
    
    image = Image.open(os.path.join(BASE_DIR, "icon.png"))

    menu = pystray.Menu(
        pystray.MenuItem("Start gesture monitoring", gesture_monitoring),
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