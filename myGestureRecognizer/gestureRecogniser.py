import time

import cv2
import os
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import GestureRecognizer, RunningMode, GestureRecognizerOptions, GestureRecognizerResult

from videoCaptureManager import video_capture_manager

WINDOW_NAME = "Hand Detection"

class VideoGestureRecogniser:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), "gesture_recognizer.task")

    def _result_callback(self, result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """
        Run for each picture analysed by the recogniser.
        """
        if len(result.gestures) < 1:
            return

        print(result.gestures[0][0].category_name)

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

    def run(self):
        """
        Turns on webcam and uses GestureRecognizer to analyse the picture.
        """
        with video_capture_manager() as cap, self._create_recognizer() as recognizer:
            while cap.isOpened():
                # get the image
                ret, frame = cap.read()
                cv2.imshow(WINDOW_NAME, frame)

                self._send_to_recogniser(frame, recognizer)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

if __name__ == "__main__":
    gr: VideoGestureRecogniser = VideoGestureRecogniser()
    gr.run()
