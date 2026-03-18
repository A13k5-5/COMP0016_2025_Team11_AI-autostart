import cv2
import time

from contextlib import contextmanager

@contextmanager
def video_capture_manager(cameraIndex: int = 0, open_retries: int = 8, retry_delay_s: float = 0.25):
    """
    Makes sure that the camera is properly turned off after the program is finished.
    Everything before the yield statement is run when entering the with statement and everything after is run when
    exiting the with statement.
    """
    cap = None
    try:
        backends = [None]
        if hasattr(cv2, "CAP_DSHOW"):
            backends.append(cv2.CAP_DSHOW)
        if hasattr(cv2, "CAP_MSMF"):
            backends.append(cv2.CAP_MSMF)

        for _ in range(max(1, open_retries)):
            for backend in backends:
                if cap is not None:
                    cap.release()

                if backend is None:
                    cap = cv2.VideoCapture(cameraIndex)
                else:
                    cap = cv2.VideoCapture(cameraIndex, backend)

                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size != 0:
                        yield cap
                        return

            time.sleep(max(0.0, retry_delay_s))

        raise RuntimeError(f"Failed to open camera index {cameraIndex} after {open_retries} retries")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
