import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECOGNIZER_STOP_SIGNAL = os.path.join(BASE_DIR, ".recognizer.stop")


def request_recognizer_stop() -> None:
    """Create a stop signal file consumed by the running recognizer controller."""
    with open(RECOGNIZER_STOP_SIGNAL, "w", encoding="utf-8") as f:
        f.write("stop")


def consume_recognizer_stop_request() -> bool:
    """Return True if a stop signal was present and remove it."""
    if not os.path.exists(RECOGNIZER_STOP_SIGNAL):
        return False
    try:
        os.remove(RECOGNIZER_STOP_SIGNAL)
    except OSError:
        return False
    return True
