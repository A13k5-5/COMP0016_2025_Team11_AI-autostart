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
            self.update_subscriber(None)
            return

        gesture_name = result.gestures[0][0].category_name
        self.update_subscriber(gesture_name)
    
    def _capture_frame(self, cap):
        """
        Capture a frame from the camera, ensure it's valid and skip frames as necessary.
        """
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0 or not self.fps_manager.is_time_for_next_frame():
            return None
        self.fps_manager.update()
        return frame
    
    def _draw_halo_effect(self, frame, box):
        """
        Draw a rounded-rectangle halo.
        """
        top, left, bottom, right = box

        h, w = frame.shape[:2]
        left = max(0, min(left, w - 1))
        right = max(0, min(right, w - 1))
        top = max(0, min(top, h - 1))
        bottom = max(0, min(bottom, h - 1))

        if right <= left or bottom <= top:
            return

        radius = int(max(1, min(18, (right - left) // 2, (bottom - top) // 2)))
        color = (80, 230, 255)  # BGR

        overlay = frame.copy()

        glow_thickness = 6
        cv2.line(overlay, (left + radius, top), (right - radius, top), color, glow_thickness, cv2.LINE_AA)
        cv2.line(overlay, (left + radius, bottom), (right - radius, bottom), color, glow_thickness, cv2.LINE_AA)
        cv2.line(overlay, (left, top + radius), (left, bottom - radius), color, glow_thickness, cv2.LINE_AA)
        cv2.line(overlay, (right, top + radius), (right, bottom - radius), color, glow_thickness, cv2.LINE_AA)
        cv2.ellipse(overlay, (left + radius, top + radius), (radius, radius), 0, 180, 270, color, glow_thickness, cv2.LINE_AA)
        cv2.ellipse(overlay, (right - radius, top + radius), (radius, radius), 0, 270, 360, color, glow_thickness, cv2.LINE_AA)
        cv2.ellipse(overlay, (right - radius, bottom - radius), (radius, radius), 0, 0, 90, color, glow_thickness, cv2.LINE_AA)
        cv2.ellipse(overlay, (left + radius, bottom - radius), (radius, radius), 0, 90, 180, color, glow_thickness, cv2.LINE_AA)

        cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)

    def _process_person_detection(self, frame):
        """
        Detect the main person in the frame and crop accordingly.
        """
        person_box = self.person_recognizer.detect_main_person(frame)
        if person_box:
            top, left, bottom, right = person_box
            top = max(0, top)
            left = max(0, left)
            bottom = min(frame.shape[0], bottom)
            right = min(frame.shape[1], right)
            self._draw_halo_effect(frame, (top, left, bottom, right))
            cropped_frame = frame[top:bottom, left:right]
            if cropped_frame.size == 0:
                return frame
            return cropped_frame
        return frame
    
    def _display_frame(self, frame):
        """
        Display the frame with gesture recognition and handle the stop condition.
        """
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.isRunning = False

    def run(self):
        """
        Main loop: capture video, detect person, crop frame, and recognize gestures.
        """
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
