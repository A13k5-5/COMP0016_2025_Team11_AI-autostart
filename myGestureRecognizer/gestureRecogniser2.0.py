import cv2

from contextlib import contextmanager

WINDOW_NAME = "Hand Detection"

@contextmanager
def video_capture_manager(cameraIndex: int = 0):
    """
    Makes sure that the camera is properly turned off after the program is finished.
    Everything before the yield statement is run when entering the with statement and everything after is run when
    exiting the with statement.
    """
    cap = cv2.VideoCapture(cameraIndex)
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {cameraIndex}")
        yield cap
    finally:
        cap.release()
        cv2.destroyAllWindows()

class GestureRecogniser:
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
    gr: GestureRecogniser = GestureRecogniser()
    gr.run()
