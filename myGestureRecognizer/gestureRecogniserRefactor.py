import argparse
import logging
import time
import os
from contextlib import contextmanager

import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "gesture_recognizer.task")
DEFAULT_CAMERA_INDEX = 0
WINDOW_NAME = "Hand Detection"


@contextmanager
def video_capture_manager(index: int):
    """
    Makes sure that the camera is properly turned off after the program is finished.
    Everything before the yield statement is run when entering the with statement and everything after is run when
    exiting the with statement.
    """
    cap = cv2.VideoCapture(index)
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {index}")
        yield cap
    finally:
        cap.release()
        # cv2.destroyAllWindows()
        pass


class GestureRecognizerApp:
    """
    Encapsulates gesture recognition lifecycle:
    - Creates a MediaPipe GestureRecognizer in LIVE_STREAM mode
    - Captures frames from a camera
    - Sends frames asynchronously to the recognizer
    - Displays frames with optional overlayed gesture names and FPS
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH, camera_index: int = DEFAULT_CAMERA_INDEX):
        self.model_path = model_path
        self.camera_index = camera_index
        self._last_gesture: str | None = None
        self._last_handedness: str | None = None
        self._last_timestamp_ms: int = 0
        self._fps = 0.0
        self._prev_time = time.time()
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    def _reset(self):
        self._last_gesture = None
        self._last_handedness = None

    def _result_callback(self, result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """
        Called by MediaPipe on the listener thread when a result is ready.
        Stores the most confident gesture name for overlaying on the next displayed frame.
        """
        if len(result.gestures) < 1:
            # then no hand detected
            self._last_gesture = None
            return
        # set the last gesture and which hand
        self._last_gesture = result.gestures[0][0].category_name
        self._last_handedness = result.handedness[0][0].category_name
        self._last_timestamp_ms = timestamp_ms
        logging.debug("Detected gesture: %s, %s at %d ms", self._last_handedness, self._last_gesture, timestamp_ms)

    def _create_recognizer(self):
        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=self._result_callback,
        )
        return GestureRecognizer.create_from_options(options)

    def run(self, gestures: list[tuple[str, str]]) -> tuple[str, str]:
        self._reset()
        logging.info("Starting GestureRecognizerApp (model=%s, camera=%d)", self.model_path, self.camera_index)
        try:
            with self._create_recognizer() as recognizer, video_capture_manager(self.camera_index) as cap:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        logging.warning("Failed to read frame from camera")
                        break

                    time.sleep(5/30)

                    # compute and update FPS
                    now = time.time()
                    dt = now - self._prev_time if now != self._prev_time else 1e-6
                    self._fps = 1.0 / dt
                    self._prev_time = now

                    timestamp_ms = int(1000 * now)

                    # convert and send to recognizer asynchronously
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    recognizer.recognize_async(mp_image, timestamp_ms)

                    # overlay last detected gesture and FPS (if any)
                    display_text = f"FPS: {self._fps:.1f}"
                    if (self._last_gesture, self._last_handedness) in gestures:
                        display_text += f" | Gesture: {self._last_gesture}, {self._last_handedness}"
                        return self._last_gesture, self._last_handedness
                    cv2.putText(frame, display_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                    cv2.imshow(WINDOW_NAME, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        logging.info("Quit key pressed")
                        break

        except Exception as exc:
            logging.exception("Unhandled error in GestureRecognizerApp: %s", exc)
        finally:
            logging.info("GestureRecognizerApp stopped")


def parse_args():
    parser = argparse.ArgumentParser(description="Live MediaPipe Gesture Recognizer")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL_PATH, help="Path to gesture recognizer model task file")
    parser.add_argument("--camera", "-c", type=int, default=DEFAULT_CAMERA_INDEX, help="Camera index (default 0)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    app = GestureRecognizerApp(model_path=args.model, camera_index=args.camera)
    input = app.run()
    print(input)