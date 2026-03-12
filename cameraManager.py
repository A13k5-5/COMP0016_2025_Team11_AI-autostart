import subprocess
import threading
from collections.abc import Callable


class CameraManager:
    """
    Manage camera handoff to external applications that need webcam access.
    """

    def __init__(self, stop_capture: Callable[[], None], resume_capture: Callable[[], None]):
        """
        Initialize handoff manager with callbacks.

        Args:
            stop_capture: Callback that stops and releases the webcam capture.
            resume_capture: Callback that rebuilds and resumes webcam capture.
        """
        self._stop_capture = stop_capture
        self._resume_capture = resume_capture
        self._handoff_lock = threading.Lock()
        self._handoff_active = False

    def handoff_to_process(self, path: str) -> None:
        """
        Start camera handoff thread for a launched app if one is not already active.
        """
        with self._handoff_lock:
            if self._handoff_active:
                return
            self._handoff_active = True

        thread = threading.Thread(target=self._handoff_worker, args=(path,), daemon=True)
        thread.start()

    def _handoff_worker(self, path: str) -> None:
        """
        Release webcam, wait for launched process exit, then resume capture.
        """
        try:
            self._stop_capture()
            subprocess.run(["cmd", "/c", "start", "/wait", "", path], check=False)
        finally:
            self._resume_capture()
            with self._handoff_lock:
                self._handoff_active = False
