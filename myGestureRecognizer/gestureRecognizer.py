import mediapipe as mp
import cv2
import time

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode


def print_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    for category in result.gestures:
        print(category[0].category_name)

# Create a gesture recognizer instance with the live stream mode:
# only livestream mode has result_callback
options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path='gesture_recognizer.task'),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Failed to open webcam")
    exit()

prev_time = 0.0

with GestureRecognizer.create_from_options(options) as recognizer:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        timestamp = int(1000 * time.time())
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        recognizer.recognize_async(mp_image, timestamp)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # show the frame
        cv2.imshow('Hand Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
