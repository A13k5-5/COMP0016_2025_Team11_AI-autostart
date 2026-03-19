import subprocess
import sys
import threading
import time
from collections.abc import Callable


class CameraManager:
    """
    Manage camera handoff to external applications that need webcam access.
    """

    def __init__(
        self,
        stop_capture: Callable[[], None],
        resume_capture: Callable[[], None],
        pre_stop_delay_s: float = 0.2,
        post_stop_delay_s: float = 0.25,
    ):
        """
        Initialize handoff manager with callbacks.

        Args:
            stop_capture: Callback that stops and releases the webcam capture.
            resume_capture: Callback that rebuilds and resumes webcam capture.
            pre_stop_delay_s: Delay before stopping capture after action trigger.
            post_stop_delay_s: Delay after stopping capture before launching app.
        """
        self._stop_capture = stop_capture
        self._resume_capture = resume_capture
        self._pre_stop_delay_s = max(0.0, float(pre_stop_delay_s))
        self._post_stop_delay_s = max(0.0, float(post_stop_delay_s))
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

        thread = threading.Thread(target=self._handoff_worker, args=(path,), daemon=False)
        thread.start()

    def is_handoff_active(self) -> bool:
        """Return True while handoff worker is active."""
        with self._handoff_lock:
            return self._handoff_active

    def _resume_capture_safe(self) -> None:
        if sys.is_finalizing():
            return
        try:
            self._resume_capture()
        except RuntimeError as exc:
            if "interpreter shutdown" in str(exc).lower():
                return
            raise

    def _handoff_worker(self, path: str) -> None:
        """
        Release webcam, wait for launched process exit, then resume capture.
        """
        exe_path = r"C:\\Users\\teole\\AI-autostart\\gameEngine\\main.dist\\main.exe"
        try:
            if self._pre_stop_delay_s > 0:
                time.sleep(self._pre_stop_delay_s)
            self._stop_capture()
            if self._post_stop_delay_s > 0:
                time.sleep(self._post_stop_delay_s)
            process = subprocess.Popen([exe_path, path])
            process.wait()
        finally:
            with self._handoff_lock:
                self._handoff_active = False
            resume_thread = threading.Thread(target=self._resume_capture_safe, daemon=False)
            resume_thread.start()