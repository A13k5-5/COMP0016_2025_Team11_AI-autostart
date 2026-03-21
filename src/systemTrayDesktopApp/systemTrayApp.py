import pystray
from PIL import Image
import sys
import os
import subprocess

from src.gui.actions import update_app_data
from src.systemTrayDesktopApp.runtimeSignals import request_recognizer_stop

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
_recognizer_process: subprocess.Popen | None = None

def _launch_script(script_name: str) -> None:
    """Launch a project script in a separate process."""
    script_path = os.path.join(PROJECT_ROOT, script_name)
    subprocess.Popen([sys.executable, script_path], cwd=PROJECT_ROOT)


def _launch_recognizer_once() -> None:
    """Launch recognizer process only when it is not already running."""
    global _recognizer_process
    if _recognizer_process is not None and _recognizer_process.poll() is None:
        print("Gesture monitoring is already running.")
        return

    script_path = os.path.join(PROJECT_ROOT, "main.py")
    _recognizer_process = subprocess.Popen([sys.executable, script_path], cwd=PROJECT_ROOT)

def exit_app(icon, item):
    icon.stop()

def gesture_monitoring(icon, item):
    _launch_recognizer_once()


def stop_gesture_monitoring(icon, item):
    global _recognizer_process
    request_recognizer_stop()
    if _recognizer_process is not None and _recognizer_process.poll() is not None:
        _recognizer_process = None

def mapping_window(icon, item):
    _launch_script("runGUI.py")

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