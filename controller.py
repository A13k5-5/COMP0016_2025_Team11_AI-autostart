import AppOpener
from myGestureRecognizer.gestureRecogniser import VideoGestureRecogniser
from gui.actions import load_mapping
from powerManager import PowerManager

class GestureController:
    """
    Coordinates gesture events, app actions, and power-mode transitions.
    """
    def __init__(self):
        self.videoGestureRecogniser: VideoGestureRecogniser = VideoGestureRecogniser(self)
        self.powerManager = PowerManager(self.videoGestureRecogniser)
        # power manager is added afterwards as a subscriber since it needs videoGestureRecogniser as an argument
        self.videoGestureRecogniser.add_subscriber(self.powerManager)

        self.prevUpdate = None

        self.gesture_mapping = load_mapping()

    def update(self, update):
        """
        Handle each recognition callback and apply LPM + action rules.
        """
        # no gesture detected
        if update is None:
            self.prevUpdate = None
            return

        # reserved for low-power mode handling in PowerManager
        if update == "Open_Palm":
            self.prevUpdate = update
            return

        if update == self.prevUpdate:
            # to prevent multiple triggers for same gesture
            return

        self.prevUpdate = update
        action = self.gesture_mapping.get(update)
        self.execute_action(action)

    def execute_action(self, action: str) -> None:
        """
        Execute an action string (open/close/stop) for a detected gesture.
        """
        if not action:
            return

        action = action.strip()
        if action == "stop":
            self.videoGestureRecogniser.stop()
            return

        if action.startswith("open:"):
            app = action.split(":", 1)[1].strip()
            if app:
                AppOpener.open(app)
            return

        if action.startswith("close:"):
            app = action.split(":", 1)[1].strip()
            if app:
                AppOpener.close(app)
            return

    def run(self):
        """
        Start the underlying video gesture recognizer loop.
        """
        self.videoGestureRecogniser.run()