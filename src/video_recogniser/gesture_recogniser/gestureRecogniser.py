import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import GestureRecognizer, RunningMode, GestureRecognizerOptions, GestureRecognizerResult

from src.video_recogniser.gesture_recogniser.fps_util import FPS
from .gestureLabels import EnumGesture
from src.video_recogniser.person_recogniser.haloEffect import draw_halo_effect
from .videoCaptureManager import video_capture_manager
from src.video_recogniser.person_recogniser.personRecogniser import PersonRecogniser

WINDOW_NAME = "AI-Autostart (Hand Gesture Recognition)"

class VideoGestureRecogniser:
    def __init__(self, controller, show_camera_view: bool = False, use_person_recognition: bool = True):
        """
        Initialize recognizer resources and subscriber list.
        """
        self.model_path = Path(__file__).parent / "gesture_recognizer.task"
        # default value of 30 fps
        self.fps_manager: FPS = FPS(30)
        self._is_low_power_mode = False
        self.subscribers = [controller] if controller is not None else []
        self.isRunning: bool = True
        self.use_person_recognition: bool = use_person_recognition

        self.person_recognizer = PersonRecogniser() if self.use_person_recognition else None
        self.show_camera_view: bool = show_camera_view

    def stop(self):
        self.isRunning = False

    def update_subscribers(self, update):
        """
        Publish the latest gesture update to all subscribers.
        """
        for subscriber in self.subscribers:
            subscriber.update(update)

    def add_subscriber(self, subscriber):
        """
        Register an additional subscriber for gesture updates.
        """
        if subscriber is not None and subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

    def set_low_power_mode(self):
        self.fps_manager.set_fps(1)
        self._is_low_power_mode = True

    def set_high_power_mode(self):
        self.fps_manager.set_fps(30)
        self._is_low_power_mode = False

    def is_low_power_mode(self) -> bool:
        """Return True when recognizer is currently in low-power mode."""
        return self._is_low_power_mode

    def _create_recognizer(self):
        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=RunningMode.LIVE_STREAM,
            result_callback=self._result_callback,
        )
        return GestureRecognizer.create_from_options(options)

    @staticmethod
    def _send_to_recogniser(frame: mp.Image, recognizer: GestureRecognizer):
        timestamp_ms = int(1000 * time.time())

        # convert and send to recognizer asynchronously
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        recognizer.recognize_async(mp_image, timestamp_ms)

    def _result_callback(self, result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """
        Run for each picture analysed by the recogniser.
        """
        if len(result.gestures) < 1:
            self.update_subscribers(None)
            return

        gesture_name = result.gestures[0][0].category_name
        handedness = ""
        if result.handedness and result.handedness[0]:
            handedness = result.handedness[0][0].category_name

        gesture = EnumGesture.from_gesture(gesture_name, handedness)
        if gesture == EnumGesture.INVALID:
            self.update_subscribers(None)
            return

        self.update_subscribers(gesture.value)
    
    def _process_person_detection(self, frame):
        """
        Detect the main person in the frame and crop accordingly.
        """
        # if in low power mode, no person recognition
        if not self.use_person_recognition or self.is_low_power_mode():
            return frame

        # lazy initialisation
        if self.person_recognizer is None:
            self.person_recognizer = PersonRecogniser()

        person_box = self.person_recognizer.detect_main_person(frame)
        if person_box:
            top, left, bottom, right = person_box
            draw_halo_effect(frame, (top, left, bottom, right))
            cropped_frame = frame[top:bottom, left:right]
            if cropped_frame.size == 0:
                return frame
            return cropped_frame
        return frame
    
    def _display_frame(self, frame):
        """
        Display the frame with gesture recognition and handle the stop condition.
        """
        if not self.show_camera_view:
            cv2.destroyAllWindows()
            return
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.isRunning = False

    def _capture_frame(self, cap):
        """
        Capture a frame from the camera, ensure it's valid and skip frames as necessary.
        """
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0 or not self.fps_manager.is_time_for_next_frame():
            return None
        self.fps_manager.update()
        return frame

    def run(self):
        """
        Main loop: capture video, detect person, crop frame, and recognize gestures.
        """
        self.isRunning = True
        with video_capture_manager() as cap, self._create_recognizer() as recognizer:
            self.fps_manager.start()

            while cap.isOpened() and self.isRunning:
                frame = self._capture_frame(cap)
                if frame is None:
                    # in low power mode
                    continue

                cropped_frame = self._process_person_detection(frame)
                self._send_to_recogniser(cropped_frame, recognizer)
                self._display_frame(frame)
