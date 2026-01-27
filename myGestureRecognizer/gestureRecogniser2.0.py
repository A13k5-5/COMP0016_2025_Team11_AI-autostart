import cv2

from videoCaptureManager import video_capture_manager

WINDOW_NAME = "Hand Detection"

class VideoGestureRecogniser:
    def __init__(self):
        pass

    def run(self):
        with video_capture_manager() as cap:
            while cap.isOpened():
                ret, frame = cap.read()
                cv2.imshow(WINDOW_NAME, frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

if __name__ == "__main__":
    gr: VideoGestureRecogniser = VideoGestureRecogniser()
    gr.run()
