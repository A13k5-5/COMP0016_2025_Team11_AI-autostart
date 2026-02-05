from openvino.runtime import Core
import numpy as np
import cv2

class PersonRecogniser:
    def __init__(self, model_path: str = "intel/person-detection-0200/FP16/person-detection-0200.xml"):
        self.ie = Core()
        self.model = self.ie.read_model(model=model_path)
        self.compiled = self.ie.compile_model(self.model, "CPU")

        self.input_layer = self.compiled.input(0)
        self.output_layer = self.compiled.output(0)

        self.input_h = self.input_layer.shape[2]
        self.input_w = self.input_layer.shape[3]

        self.detect_every_n_frames = 3
        self._frame_counter = 0
        self._last_box = None

    def detect_main_person(self, frame):
        self._frame_counter += 1
        if self._frame_counter % self.detect_every_n_frames != 0:
            return self._last_box 

        h, w, _ = frame.shape
        resized = cv2.resize(frame, (self.input_w, self.input_h))
        inp = np.expand_dims(resized.transpose(2, 0, 1), 0).astype(np.uint8)

        results = self.compiled([inp])[self.output_layer]
        boxes = []

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

        self._last_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))[:4]
        return self._last_box
