import time


class FPS:
    def __init__(self, setFps: int = 0):
        self._start = None
        self._prev: float = 0
        self._numFrames = 0
        self._setFps: int = setFps

    def set_fps(self, newFps: int):
        self._setFps = newFps

    def start(self):
        self._start = time.time()
        return self

    def update(self):
        self._numFrames += 1

    def elapsed_since_last_frame(self):
        return time.time() - self._prev

    def elapsed_seconds(self):
        return time.time() - self._start

    def get_current_fps(self):
        return self._numFrames / self.elapsed_seconds()

    def is_time_for_next_frame(self) -> bool:
        """
        Uses the time since last frame to determine if it's time for next frame.
        """
        if self.elapsed_since_last_frame() > 1./self._setFps:
            self._prev = time.time()
            return True
        return False
