import json
import os
import AppOpener

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MAPPING_PATH = os.path.join(BASE_DIR, "gui", "gesture_mapping.json")

SUPPORTED_ACTIONS = [
    "open:zen",
    "close:zen",
    "open:notepad",
    "close:notepad",
    "stop",
]

SUPPORTED_GESTURES = [
    "Pointing_Up",
    "Closed_Fist",
    "Victory",
    "ILoveYou",
    "Thumb_Up",
    "Thumb_Down",
]

# reserved for LPM activation
RESERVED_GESTURES = {"Open_Palm"}

def load_mapping(path: str = MAPPING_PATH) -> dict:
    """
    Load and return the persisted gesture-to-action mapping from JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {g: str(data[g]).strip() for g in SUPPORTED_GESTURES}

def save_mapping(mapping: dict, path: str = MAPPING_PATH) -> None:
    """
    Persist the provided gesture-to-action mapping to JSON.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = {g: str(mapping.get(g, "")).strip() for g in SUPPORTED_GESTURES}
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

def execute_action(action: str, video_gesture_recogniser) -> None:
    """
    Execute an action string (open/close/stop) for a detected gesture.
    """
    if not action:
        return

    action = action.strip()
    if action == "stop":
        video_gesture_recogniser.stop()
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