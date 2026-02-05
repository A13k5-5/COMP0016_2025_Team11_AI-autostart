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
        self.stop_requested = False
        self.latest_gesture = None

    def stop(self):
        print("Stopping Gesture Recogniser...")
        self.isRunning = False
        if hasattr(self, 'recognizer') and self.recognizer is not None:
            self.recognizer.close()

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
        if len(result.gestures) < 1:
            self.latest_gesture = None
            return

        gesture_name = result.gestures[0][0].category_name
        self.latest_gesture = gesture_name

        if gesture_name == "Thumb_Down":
            self.stop_requested = True

        self.update_subscriber(gesture_name)

    def run(self):
        """
        Main loop: capture video, detect person, crop frame, and recognize gestures.
        """
        self.stop_requested = False
        self.recognizer = self._create_recognizer()
        self.fps_manager.start()

        with video_capture_manager() as cap:
            while cap.isOpened() and self.isRunning:
                ret, frame = cap.read()
                if not ret or frame is None or frame.size == 0:
                    continue

                if not self.fps_manager.is_time_for_next_frame():
                    continue

                self.fps_manager.update()

                person_box = self.person_recognizer.detect_main_person(frame)
                if person_box:
                    top, left, bottom, right = person_box

                    top = max(0, top)
                    left = max(0, left)
                    bottom = min(frame.shape[0], bottom)
                    right = min(frame.shape[1], right)

                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cropped_frame = frame[top:bottom, left:right]

                    if cropped_frame.size == 0:
                        cropped_frame = frame
                else:
                    cropped_frame = frame 

                try:
                    self._send_to_recogniser(cropped_frame, self.recognizer)
                except Exception as e:
                    print(f"Warning: recognizer failed for this frame: {e}")

                if self.latest_gesture:
                    cv2.putText(frame, self.latest_gesture, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                                1.2,(0, 0, 255), 2, cv2.LINE_AA)
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_requested = True

                if self.stop_requested:
                    self.isRunning = False

            if hasattr(self, "recognizer") and self.recognizer is not None:
                try:
                    self.recognizer.close()
                except Exception as e:
                    print(f"Warning: failed to close recognizer cleanly: {e}")

            cv2.destroyAllWindows()
