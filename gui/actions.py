import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MAPPING_PATH = os.path.join(BASE_DIR, "gui", "gesture_mapping.json")

SUPPORTED_ACTIONS = [
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

# Prefix used for user-defined executable actions stored in the mapping file.
RUN_PREFIX = "run:"
RUN_USES_CAMERA_KEY = "run_uses_camera"

def is_run_action(action: str) -> bool:
    """Return True if *action* represents a user-chosen file to open."""
    return action.startswith(RUN_PREFIX)


def make_run_action(path: str) -> str:
    """Build a run action string from a file path."""
    return f"{RUN_PREFIX}{path.strip()}"


def get_run_path(action: str) -> str:
    """Extract the file path from a run action string."""
    return action[len(RUN_PREFIX):]


def load_mapping(path: str = MAPPING_PATH) -> dict:
    """
    Load and return the persisted gesture-to-action mapping from JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {g: str(data.get(g, "")).strip() for g in SUPPORTED_GESTURES}

def load_run_uses_camera(path: str = MAPPING_PATH) -> bool:
    """
    Load the persisted camera-use flag for the run action row.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return bool(data.get(RUN_USES_CAMERA_KEY, False))

def save_mapping(mapping: dict, path: str = MAPPING_PATH, run_uses_camera: bool = False) -> None:
    """
    Persist the provided gesture-to-action mapping to JSON.
    """
    out = {g: str(mapping.get(g, "")).strip() for g in SUPPORTED_GESTURES}
    out[RUN_USES_CAMERA_KEY] = bool(run_uses_camera)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
