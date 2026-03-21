import subprocess
import time
from collections.abc import Callable


class CameraManager:
    """
    Manage camera handoff to external applications that need webcam access.
    """

    def __init__(
        self,
        stop_capture: Callable[[], bool],
        resume_capture: Callable[[], None],
        pre_stop_delay_s: float = 0.2,
        post_stop_delay_s: float = 3.25,
    ):
        """
        Initialize handoff manager with callbacks.

        Args:
            stop_capture: Callback that blocks until webcam capture is fully stopped.
            resume_capture: Callback that rebuilds and resumes webcam capture.
            pre_stop_delay_s: Delay before stopping capture after action trigger.
            post_stop_delay_s: Delay after stopping capture before launching app.
        """
        self._stop_capture = stop_capture
        self._resume_capture = resume_capture
        self._pre_stop_delay_s = max(0.0, float(pre_stop_delay_s))
        self._post_stop_delay_s = max(0.0, float(post_stop_delay_s))
        self._handoff_active = False

    def handoff_to_process(self, path: str) -> None:
        """
        Perform synchronous camera handoff for a launched app.
        """
        if self._handoff_active:
            return

        self._handoff_active = True
        try:
            if self._pre_stop_delay_s > 0:
                time.sleep(self._pre_stop_delay_s)
            stopped = self._stop_capture()
            if not stopped:
                print("Stop capture timed out. Launch cancelled.")
                return
            if self._post_stop_delay_s > 0:
                time.sleep(self._post_stop_delay_s)
            print("Launching.")
            subprocess.run(["cmd", "/c", "start", "/wait", "", path], check=False)
        finally:
            self._handoff_active = False
            self._resume_capture()