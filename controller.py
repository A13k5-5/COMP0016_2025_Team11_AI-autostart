import os
import threading
from time import time, sleep
import AppOpener
from myGestureRecognizer.gestureRecogniser import VideoGestureRecogniser
from gui.actions import (
    MAPPING_PATH,
    load_mapping,
    load_run_uses_camera,
    load_camera_view_enabled,
    load_person_recognition_enabled,
    is_run_action,
    get_run_path,
)
from powerManager import PowerManager
from cameraManager import CameraManager
from runtimeSignals import consume_recognizer_stop_request

class GestureController:
    """
    Coordinates gesture events, app actions, and power-mode transitions.
    """
    def __init__(self):
        self.camera_view_enabled = load_camera_view_enabled()
        self.person_recognition_enabled = load_person_recognition_enabled()
        self.videoGestureRecogniser: VideoGestureRecogniser = VideoGestureRecogniser(
            self,
            show_camera_view=self.camera_view_enabled,
            use_person_recognition=self.person_recognition_enabled,
        )
        self.powerManager = PowerManager(self.videoGestureRecogniser)
        # power manager is added afterwards as a subscriber since it needs videoGestureRecogniser as an argument
        self.videoGestureRecogniser.add_subscriber(self.powerManager)
        self._resume_requested = threading.Event()
        self.cameraManager = CameraManager(
            stop_capture=lambda: self.videoGestureRecogniser.stop(wait=True),
            resume_capture=self._request_resume_after_handoff,
            pre_stop_delay_s=0.2,
            post_stop_delay_s=0.25,
        )

        self.prevUpdate = None
        self.last_gesture_detected_at = 0.0
        self.gesture_dropout_grace_seconds = 0.8

        self.gesture_mapping = load_mapping()
        self.run_uses_camera = load_run_uses_camera()
        self._mapping_mtime = self._get_mapping_mtime()

    def _rebuild_recogniser(self) -> None:
        """
        Create a fresh recognizer instance and rewire subscribers.
        """
        self.videoGestureRecogniser = VideoGestureRecogniser(
            self,
            show_camera_view=self.camera_view_enabled,
            use_person_recognition=self.person_recognition_enabled,
        )
        self.powerManager = PowerManager(self.videoGestureRecogniser)
        self.videoGestureRecogniser.add_subscriber(self.powerManager)
        self.prevUpdate = None

    def _request_resume_after_handoff(self) -> None:
        """Signal that recognizer should be resumed after handoff completion."""
        self._resume_requested.set()

    def _resume_capture_after_handoff(self) -> None:
        """
        Rebuild recognizer after external app exits.
        """
        self._rebuild_recogniser()

    def _project_root(self) -> str:
        """Return absolute path to the project root."""
        return os.path.dirname(os.path.abspath(__file__))

    def _get_mapping_mtime(self) -> float:
        """Return gesture mapping file modified time (0.0 when unavailable)."""
        try:
            return os.path.getmtime(MAPPING_PATH)
        except OSError:
            return 0.0

    def _reload_runtime_settings_if_needed(self) -> None:
        """Hot-reload runtime settings when gesture mapping file changes."""
        current_mtime = self._get_mapping_mtime()
        if current_mtime <= self._mapping_mtime:
            return

        self._mapping_mtime = current_mtime
        self.gesture_mapping = load_mapping()
        self.run_uses_camera = load_run_uses_camera()
        self.camera_view_enabled = load_camera_view_enabled()
        self.person_recognition_enabled = load_person_recognition_enabled()
        self.videoGestureRecogniser.show_camera_view = self.camera_view_enabled
        self.videoGestureRecogniser.use_person_recognition = self.person_recognition_enabled

    def _resolve_launch_path(self, path: str) -> str:
        """
        Resolve a run-action path into an absolute filesystem path.

        Stored run paths are often project-relative (e.g. ../Downloads/foo.noui).
        """
        expanded = os.path.expandvars(os.path.expanduser(path.strip()))
        if os.path.isabs(expanded):
            return expanded
        return os.path.abspath(os.path.join(self._project_root(), expanded))

    def update(self, update: str | None):
        """
        Handle each recognition callback and apply LPM + action rules.

        Args:
            update: Detected gesture name, or None when no gesture is detected.
        """
        self._reload_runtime_settings_if_needed()
        if consume_recognizer_stop_request():
            self.videoGestureRecogniser.stop()
            return

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
                launch_path = self._resolve_launch_path(path)
                if not os.path.exists(launch_path):
                    print(f"Run target not found: {launch_path}")
                    return
                if self.run_uses_camera:
                    self.cameraManager.handoff_to_process(launch_path)
                else:
                    os.startfile(launch_path)
            return

    def run(self):
        """
        Start recognizer loop and handle handoff-triggered restarts in this thread.
        """
        while True:
            self.videoGestureRecogniser.run()

            while self.cameraManager.is_handoff_active() and not self._resume_requested.is_set():
                sleep(0.1)

            if self._resume_requested.is_set():
                self._resume_requested.clear()
                self._resume_capture_after_handoff()
                continue

            break