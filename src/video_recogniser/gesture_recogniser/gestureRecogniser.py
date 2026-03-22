import time
import threading

import cv2
import os
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import GestureRecognizer, RunningMode, GestureRecognizerOptions, GestureRecognizerResult

from src.video_recogniser.gesture_recogniser.fps_util import FPS
from .gestureLabels import EnumGesture
# from src.video_recogniser.person_recogniser.haloEffect import draw_halo_effect
from .videoCaptureManager import video_capture_manager
# from src.video_recogniser.person_recogniser.personRecogniser import PersonRecogniser

WINDOW_NAME = "Hand Detection"

class VideoGestureRecogniser:
    def __init__(self, controller, show_camera_view: bool = False, use_person_recognition: bool = True):
        """
        Initialize recognizer resources and subscriber list.
        """
        self.model_path = os.path.join(os.path.dirname(__file__), "gesture_recognizer.task")
        # default value of 30 fps
        self.fps_manager = FPS(30)
        self._is_low_power_mode = False
        self.subscribers = [controller]
        self.isRunning = True
        self._stopped_event = threading.Event()
        self._stopped_event.set()
        # self.use_person_recognition = bool(use_person_recognition)
        self.use_person_recognition = False
        # self.person_recognizer = PersonRecogniser() if self.use_person_recognition else None
        self.person_recognizer = None
        self.show_camera_view = bool(show_camera_view)

    def wait_until_stopped(self, timeout: float = 3.0, poll_interval_s: float = 0.02) -> bool:
        """
        Block until the recognizer loop has fully stopped.

        Returns:
            True when run loop has exited within timeout, otherwise False.
        """
        timeout = max(0.0, float(timeout))
        poll_interval_s = max(0.005, float(poll_interval_s))
        deadline = time.time() + timeout

        while True:
            if self._stopped_event.is_set() and not self.isRunning:
                return True

            remaining = deadline - time.time()
            if remaining <= 0:
                break

            self._stopped_event.wait(timeout=min(poll_interval_s, remaining))

        return self._stopped_event.is_set() and not self.isRunning

    def stop(self, wait: bool = False, timeout: float = 3.0) -> bool:
        print("Stopping Gesture Recogniser...")
        self.isRunning = False
        if wait:
            return self.wait_until_stopped(timeout=max(0.0, timeout))
        return self._stopped_event.is_set() and not self.isRunning
    
    def restart(self):
        print("Restarting Gesture Recogniser...")
        self.isRunning = True
        self.run()

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
    
    def _capture_frame(self, cap):
        """
        Capture a frame from the camera, ensure it's valid and skip frames as necessary.
        """
        try:
            ret, frame = cap.read()
        except cv2.error:
            return None
        if not ret or frame is None or frame.size == 0 or not self.fps_manager.is_time_for_next_frame():
            return None
        self.fps_manager.update()
        return frame
    
    def _process_person_detection(self, frame):
        """
        Detect the main person in the frame and crop accordingly.
        """
        if not self.use_person_recognition:
            return frame

        # if self.person_recognizer is None:
        #     self.person_recognizer = PersonRecogniser()

        person_box = self.person_recognizer.detect_main_person(frame)
        if person_box:
            top, left, bottom, right = person_box
            top = max(0, top)
            left = max(0, left)
            bottom = min(frame.shape[0], bottom)
            right = min(frame.shape[1], right)
            # draw_halo_effect(frame, (top, left, bottom, right))
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
            return
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.isRunning = False

    def run(self):
        """
        Main loop: capture video, detect person, crop frame, and recognize gestures.
        """
        self._stopped_event.clear()
        try:
            with video_capture_manager() as cap, self._create_recognizer() as recognizer:
                self.fps_manager.start()

                while cap.isOpened() and self.isRunning:
                    frame = self._capture_frame(cap)
                    if frame is None:
                        continue

                    cropped_frame = self._process_person_detection(frame)
                    self._send_to_recogniser(cropped_frame, recognizer)
                    self._display_frame(frame)

                cv2.destroyAllWindows()
        finally:
            self._stopped_event.set()
