import datetime

class FPS:
    def __init__(self):
        self._start = None
        self._numFrames = 0

    def start(self):
        self._start = datetime.datetime.now()
        return self

    def update(self):
        self._numFrames += 1

    def elapsed(self):
        return (datetime.datetime.now() - self._start).total_seconds()

    def fps(self):
        return self._numFrames / self.elapsed()
