from openvino.runtime import Core
import numpy as np

class PersonRecognizer:
    def __init__(self, model_path: str = "intel/person-detection-0200/FP16/person-detection-0200.xml"):
        self.ie = Core()
        self.model = self.ie.read_model(model_path)
        self.compiled = self.ie.compile_model(self.model, "CPU")
        self.input_layer = self.compiled.input(0)
        self.output_layer = self.compiled.output(0)

    def detect_main_person(self, frame):
        h, w, _ = frame.shape
        resized = cv2.resize(frame, (256, 256))
        inp = np.expand_dims(resized.transpose(2, 0, 1), 0).astype(np.float32)

        results = self.compiled([inp])[self.output_layer]
        boxes = []

        for obj in results[0][0]:
            _, conf, xmin, ymin, xmax, ymax = obj
            if conf > 0.6:
                boxes.append((
                    int(ymin * h), int(xmin * w),
                    int(ymax * h), int(xmax * w),
                    conf
                ))
        if not boxes:
            return None

        return max(boxes, key=lambda b: (b[2]-b[0])*(b[3]-b[1]))[:4]