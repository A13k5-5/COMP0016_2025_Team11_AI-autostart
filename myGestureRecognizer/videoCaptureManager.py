import cv2

from contextlib import contextmanager

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
