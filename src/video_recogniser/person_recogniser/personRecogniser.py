from openvino.runtime import Core
import numpy as np
import cv2
from src.video_recogniser.gesture_recogniser.fps_util import FPS
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "intel" / "person-detection-0200" / "FP16" / "person-detection-0200.xml"

class PersonRecogniser:
    def __init__(self, model_path: Path | str = MODEL_PATH):

        # Initialize OpenVINO runtime and load the person detection model
        self.ie = Core()
        self.model = self.ie.read_model(model=model_path)
        self.compiled = self.ie.compile_model(self.model, "CPU")

        self.input_layer = self.compiled.input(0)
        self.output_layer = self.compiled.output(0)
        self.input_h = self.input_layer.shape[2]
        self.input_w = self.input_layer.shape[3]

        # default value of 30 fps
        self.fps_manager = FPS(30)
        self.fps_manager.start()
        self._last_box = None

    def detect_main_person(self, frame):
        """
        Detect the main person in the frame.
        Returns a bounding box (top, left, bottom, right) or None if no person detected.
        Uses FPS manager to skip frames for performance.
        """
        if not self.fps_manager.is_time_for_next_frame():
            return self._last_box

        # Resize frame to model input
        h, w, _ = frame.shape
        resized = cv2.resize(frame, (self.input_w, self.input_h))
        inp = np.expand_dims(resized.transpose(2, 0, 1), 0).astype(np.uint8)

        results = self.compiled([inp])[self.output_layer]
        boxes = []

        # Process results and filter by confidence
        for obj in results[0][0]:
            _, _, conf, xmin, ymin, xmax, ymax = obj
            if conf > 0.6:
                boxes.append((
                    int(ymin * h), int(xmin * w),
                    int(ymax * h), int(xmax * w),
                    conf
                ))

        if not boxes:
            return self._last_box

        # Return the largest detected person
        self._last_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))[:4]
        return self._last_box
