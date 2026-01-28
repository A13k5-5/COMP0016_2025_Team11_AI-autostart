import AppOpener
from myGestureRecognizer.gestureRecogniser import VideoGestureRecogniser


class GestureController:
    def __init__(self):
        self.videoGestureRecogniser: VideoGestureRecogniser = VideoGestureRecogniser(self)
        self.prevUpdate = None

    def update(self, update):
        if update == self.prevUpdate:
            # to prevent multiple triggers for same gesture
            return
        self.prevUpdate = update
        match update:
            case "Open_Palm":
                AppOpener.open("zen")
            case "Closed_Fist":
                AppOpener.close("zen")
            case "Victory":
                AppOpener.open("steam")
            case "ILoveYou":
                AppOpener.close("steam")
            case "Thumb_Up":
                self.videoGestureRecogniser.stop()

    def run(self):
        self.videoGestureRecogniser.run()
