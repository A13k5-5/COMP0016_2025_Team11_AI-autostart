from myGestureRecognizer.gestureRecogniser import VideoGestureRecogniser


class GestureController:
    def __init__(self):
        self.videoGestureRecogniser: VideoGestureRecogniser = VideoGestureRecogniser(self)

    def update(self, update):
        print("Controller received update: ", update)

    def run(self):
        self.videoGestureRecogniser.run()
