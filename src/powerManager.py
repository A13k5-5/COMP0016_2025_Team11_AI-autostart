from config import open_palm_hold_seconds, inactivity_timeout_seconds
from time import time
from myGestureRecognizer.gestureLabels import EnumGesture

class PowerManager:
    """
    Manage low-power/high-power transitions based on gesture activity.
    """

    def __init__(self, videoGestureRecogniser):
        """
        Initialize timing state and start in low-power mode.
        """
        self.videoGestureRecogniser = videoGestureRecogniser
        self.videoGestureRecogniser.set_low_power_mode()
        self.last_gesture_time = time()
        self.open_palm_start_time = None

    def update(self, update: str | None):
        """
        Handle gesture stream updates and apply low-power transitions.

        Args:
            update: Detected gesture name, or None when no gesture is detected.
        """
        now = time()

        # no gesture detected
        if update is None:
            self.open_palm_start_time = None
            self.try_activate_LPM(now)
            return

        self.last_gesture_time = now

        # open palm must be held continuously to deactivate LPM
        if update in {EnumGesture.OPEN_PALM.value, "Open_Palm"}:
            if self.open_palm_start_time is None:
                self.open_palm_start_time = now

            self.try_deactivate_LPM(now)
            return

        # other gestures interrupt the hold timer
        self.open_palm_start_time = None

    def deactivate_LPM(self):
        self.videoGestureRecogniser.set_high_power_mode()

    def try_deactivate_LPM(self, now):
        """
        Switch to high-power mode after a sustained open-palm hold.
        """
        if (
            self.videoGestureRecogniser.is_low_power_mode()
            and self.open_palm_start_time is not None
            and (now - self.open_palm_start_time) >= open_palm_hold_seconds
        ):
            self.deactivate_LPM()

    def activate_LPM(self):
        self.videoGestureRecogniser.set_low_power_mode()

    def try_activate_LPM(self, now):
        """
        Switch to low-power mode after prolonged gesture inactivity.
        """
        if not self.videoGestureRecogniser.is_low_power_mode() and (now - self.last_gesture_time >= inactivity_timeout_seconds):
            self.activate_LPM()