import time


class FPS:
    def __init__(self):
        self._start = None
        self._prev: float = 0
        self._numFrames = 0

    def start(self):
        self._start = time.time()
        return self

    def update(self):
        self._numFrames += 1

    def elapsed_since_last_frame(self):
        return time.time() - self._prev

    def elapsed_seconds(self):
        return (time.time() - self._start).total_seconds()

    def get_current_fps(self):
        return self._numFrames / self.elapsed_seconds()
