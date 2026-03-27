import os
import subprocess
from time import time
import AppOpener
from src.video_recogniser.gesture_recogniser.gestureRecogniser import VideoGestureRecogniser
from src.video_recogniser.gesture_recogniser.gestureLabels import EnumGesture
from src.gui.actions import (
    MAPPING_PATH,
    load_mapping,
    load_run_uses_camera,
    load_camera_view_enabled,
    load_person_recognition_enabled,
    is_run_action,
    get_run_path,
    path_uses_camera
)
from src.controller.powerManager import PowerManager

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

        self.prevUpdate = None
        self.last_gesture_detected_at = 0.0
        self.gesture_dropout_grace_seconds = 0.8

        self.gesture_mapping = load_mapping()
        self.run_uses_camera = load_run_uses_camera()

        self.path_to_run = None
        self.path_was_run = False


    def reload_runtime_settings_if_needed(self) -> None:
        """Hot-reload runtime settings when gesture mapping file changes."""

        self.gesture_mapping = load_mapping()
        self.run_uses_camera = load_run_uses_camera()
        self.camera_view_enabled = load_camera_view_enabled()
        self.person_recognition_enabled = load_person_recognition_enabled()
        self.videoGestureRecogniser.use_person_recognition = load_person_recognition_enabled()
        self.videoGestureRecogniser.show_camera_view = load_camera_view_enabled()

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
        if update == EnumGesture.OPEN_PALM.value:
            self.prevUpdate = update
            return

        if update == self.prevUpdate:
            # to prevent multiple triggers for same gesture
            return

        self.prevUpdate = update
        action = self.gesture_mapping.get(update)
        self.execute_action(action)

    def run_file_and_wait(self) -> None:
        if self.path_to_run is None:
            return

        try:
            subprocess.run(
                ["cmd", "/c", "start", "", "/wait", self.path_to_run],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        finally:
            self.path_to_run = None

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
            self.stop()
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
                self.path_to_run = path
                if path_uses_camera(path):
                    self.videoGestureRecogniser.stop()
                else:
                    os.startfile(path)
            return

    def stop(self):
        """Stop the recognizer loop."""
        self.videoGestureRecogniser.stop()
        self.path_to_run = None

    def run(self):
        """
        Start recognizer loop and handle handoff-triggered restarts in this thread.
        """
        while True:
            self.videoGestureRecogniser.run()

            # the recogniser was stopped to run a file that requires camera access
            if self.path_to_run is not None:
                self.run_file_and_wait()
            else:
            # the recogniser was stopped naturally
                break
