import subprocess
import threading
import time
from collections.abc import Callable
import cv2


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

    @staticmethod
    def _camera_is_readable(camera_index: int = 0) -> bool:
        """Return True when a quick camera open/read succeeds."""
        cap = cv2.VideoCapture(camera_index)
        try:
            if not cap.isOpened():
                return False
            ret, frame = cap.read()
            return bool(ret and frame is not None and frame.size != 0)
        except cv2.error:
            return False
        finally:
            cap.release()

    def _wait_for_camera_usage_cycle(
        self,
        startup_timeout_s: float = 8.0,
        poll_interval_s: float = 0.35,
        release_timeout_s: float = 600.0,
    ) -> None:
        """
        Wait for launched app to use camera (busy) and then release it (free).

        This prevents immediate recognizer resume when process launch returns before
        the real camera-consuming game process exits.
        """
        deadline = time.time() + max(0.0, startup_timeout_s)
        seen_busy = False

        while time.time() < deadline:
            if not self._camera_is_readable():
                seen_busy = True
                break
            time.sleep(max(0.05, poll_interval_s))

        if not seen_busy:
            return

        release_deadline = time.time() + max(0.0, release_timeout_s)
        while time.time() < release_deadline:
            if self._camera_is_readable():
                return
            time.sleep(max(0.05, poll_interval_s))

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
            time.sleep(0.35)
            subprocess.run(["cmd", "/c", "start", "/wait", "", path], check=False)
            self._wait_for_camera_usage_cycle()
        finally:
            self._resume_capture()
            with self._handoff_lock:
                self._handoff_active = False
