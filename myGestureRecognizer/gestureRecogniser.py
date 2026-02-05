import time

import cv2
import os
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import GestureRecognizer, RunningMode, GestureRecognizerOptions, GestureRecognizerResult

from .fps import FPS
from .videoCaptureManager import video_capture_manager
from .personRecogniser import PersonRecogniser

WINDOW_NAME = "Hand Detection"

class VideoGestureRecogniser:
    def __init__(self, controller):
        self.model_path = os.path.join(os.path.dirname(__file__), "gesture_recognizer.task")
        # default value of 30 fps
        self.fps_manager = FPS(30)
        self.subscriber = controller
        self.isRunning = True
        self.person_recognizer = PersonRecogniser()

    def stop(self):
        print("Stopping Gesture Recogniser...")
        self.isRunning = False

    def update_subscriber(self, update):
        self.subscriber.update(update)

    def set_low_power_mode(self):
        self.fps_manager.set_fps(1)

    def set_high_power_mode(self):
        self.fps_manager.set_fps(30)

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
            return

        self.update_subscriber(result.gestures[0][0].category_name)

    def run(self):
        with video_capture_manager() as cap, self._create_recognizer() as recognizer:
            self.fps_manager.start()
            while cap.isOpened() and self.isRunning:
                ret, frame = cap.read()
                if not ret:
                    continue

                if not self.fps_manager.is_time_for_next_frame():
                    continue

                self.fps_manager.update()

                person_box = self.person_detector.detect_main_person(frame)
                if person_box:
                    top, left, bottom, right = person_box

                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                else:
                    cropped_frame = frame  # fallback to full frame

                # send cropped frame to recognizer
                self._send_to_recogniser(cropped_frame, recognizer)

                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop()
