from time import time
import AppOpener
from myGestureRecognizer.gestureRecogniser import VideoGestureRecogniser
from gui.actions import load_mapping, execute_action

class GestureController:
    """
    Coordinates gesture events, app actions, and power-mode transitions.
    """
    def __init__(self):
        self.videoGestureRecogniser: VideoGestureRecogniser = VideoGestureRecogniser(self)
        self.prevUpdate = None
        self.last_gesture_time = time()
        self.low_power = True
        self.open_palm_start_time = None

        self.open_palm_hold_seconds = 2
        self.inactivity_timeout_seconds = 30

        self.gesture_mapping = load_mapping()

    def update(self, update):
        """
        Handle each recognition callback and apply LPM + action rules.
        """
        now = time()

        # no gesture detected
        if update is None:
            self.prevUpdate = None
            self.open_palm_start_time = None
            self.activate_LPM(now)
            return

        self.last_gesture_time = now

        # open palm must be held continuously to deactivate LPM
        if update == "Open_Palm":
            if self.open_palm_start_time is None:
                # mark the start of hold-to-wake gesture
                self.open_palm_start_time = now

            self.deactivate_LPM(now)
            self.prevUpdate = update
            return

        # other gestures interrupt the hold timer
        self.open_palm_start_time = None

        if update == self.prevUpdate:
            # to prevent multiple triggers for same gesture
            return

        self.prevUpdate = update
        action = self.gesture_mapping.get(update, "")
        execute_action(action, self.videoGestureRecogniser)

    def run(self):
        """
        Start the underlying video gesture recognizer loop.
        """
        self.videoGestureRecogniser.run()

    def deactivate_LPM(self, now=None):
        """
        Switch to high-power mode after a sustained open-palm hold.
        """
        if now is None:
            now = time()
        if (
            self.low_power
            and self.open_palm_start_time is not None
            and (now - self.open_palm_start_time) >= self.open_palm_hold_seconds
        ):
            self.videoGestureRecogniser.set_high_power_mode()
            self.low_power = False

    def activate_LPM(self, now=None):
        """
        Switch to low-power mode after prolonged gesture inactivity.
        """
        if now is None:
            now = time()

        if not self.low_power and (now - self.last_gesture_time >= self.inactivity_timeout_seconds):
            self.videoGestureRecogniser.set_low_power_mode()
            self.low_power = True