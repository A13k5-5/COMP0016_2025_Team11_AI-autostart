import os
from time import time
import AppOpener
from myGestureRecognizer.gestureRecogniser import VideoGestureRecogniser
from gui.actions import load_mapping, load_run_uses_camera, is_run_action, get_run_path
from powerManager import PowerManager
from cameraManager import CameraManager

class GestureController:
    """
    Coordinates gesture events, app actions, and power-mode transitions.
    """
    def __init__(self):
        self.videoGestureRecogniser: VideoGestureRecogniser = VideoGestureRecogniser(self)
        self.powerManager = PowerManager(self.videoGestureRecogniser)
        # power manager is added afterwards as a subscriber since it needs videoGestureRecogniser as an argument
        self.videoGestureRecogniser.add_subscriber(self.powerManager)
        self.cameraManager = CameraManager(
            stop_capture=lambda: self.videoGestureRecogniser.stop(),
            resume_capture=self._resume_capture_after_handoff,
        )

        self.prevUpdate = None
        self.last_gesture_detected_at = 0.0
        self.gesture_dropout_grace_seconds = 0.8

        self.gesture_mapping = load_mapping()
        self.run_uses_camera = load_run_uses_camera()

    def _rebuild_recogniser(self) -> None:
        """
        Create a fresh recognizer instance and rewire subscribers.
        """
        self.videoGestureRecogniser = VideoGestureRecogniser(self)
        self.powerManager = PowerManager(self.videoGestureRecogniser)
        self.videoGestureRecogniser.add_subscriber(self.powerManager)
        self.prevUpdate = None

    def _resume_capture_after_handoff(self) -> None:
        """
        Rebuild recognizer and resume capture after external app exits.
        """
        self._rebuild_recogniser()
        self.videoGestureRecogniser.run()

    def update(self, update: str | None):
        """
        Handle each recognition callback and apply LPM + action rules.

        Args:
            update: Detected gesture name, or None when no gesture is detected.
        """
        now = time()

        # no gesture detected
        if update is None:
            if (
                self.prevUpdate is not None
                and (now - self.last_gesture_detected_at) >= self.gesture_dropout_grace_seconds
            ):
                self.prevUpdate = None
            return

        self.last_gesture_detected_at = now

        # reserved for low-power mode handling in PowerManager
        if update == "Open_Palm":
            self.prevUpdate = update
            return

        if update == self.prevUpdate:
            # to prevent multiple triggers for same gesture
            return

        self.prevUpdate = update
        action = self.gesture_mapping.get(update)
        self.execute_action(action)

    def execute_action(self, action: str) -> None:
        """
        Execute one action using the project's action-text format.

        Supported values:
            - "stop"
            - "open:<app_name>"
            - "close:<app_name>"
            - "run:<path_to_executable>"

        Args:
            action: Action text looked up from gesture_mapping.json for the
                current gesture.
        """
        if not action:
            return

        action = action.strip()
        if action == "stop":
            self.videoGestureRecogniser.stop()
            return

        if action.startswith("open:"):
            app = action.split(":", 1)[1].strip()
            if app:
                AppOpener.open(app)
            return

        if action.startswith("close:"):
            app = action.split(":", 1)[1].strip()
            if app:
                AppOpener.close(app)
            return

        if is_run_action(action):
            path = get_run_path(action)
            if path:
                if self.run_uses_camera:
                    self.cameraManager.handoff_to_process(path)
                else:
                    os.startfile(path)
            return

    def run(self):
        """
        Start the underlying video gesture recognizer loop.
        """
        self.videoGestureRecogniser.run()