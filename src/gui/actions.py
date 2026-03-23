import json
from src.video_recogniser.gesture_recogniser.gestureLabels import (
    EnumGesture,
    SUPPORTED_GESTURES as CANONICAL_SUPPORTED_GESTURES,
)
from pathlib import Path
import AppOpener

SRC_DIR = Path(__file__).parent.parent
MAPPING_PATH = SRC_DIR / "gesture_mapping.json"
APP_DATA_PATH = SRC_DIR / "app_data.json"

SUPPORTED_ACTIONS = [
    "stop",
]

SUPPORTED_GESTURES = list(CANONICAL_SUPPORTED_GESTURES)

# reserved for LPM activation
RESERVED_GESTURES = {EnumGesture.OPEN_PALM.value}

# Prefix used for user-defined executable actions stored in the mapping file.
RUN_PREFIX = "run:"
RUN_USES_CAMERA_KEY = "run_uses_camera"  # kept for backward-compat loading
GAME_RUN_PATH_KEY = "game_run_path"       # kept for backward-compat loading
GAME_RUN_PATHS_KEY = "game_run_paths"
FILE_RUN_ENTRIES_KEY = "file_run_entries"
DYNAMIC_APPS_KEY = "dynamic_apps"
CAMERA_VIEW_ENABLED_KEY = "camera_view_enabled"
PERSON_RECOGNITION_ENABLED_KEY = "person_recognition_enabled"

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

def load_app_data(path: str = APP_DATA_PATH) -> dict:
    """
    Load app_data.json and return the app-name -> app-id mapping.
    """
    if not path.exists():
        update_app_data()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_app_data() -> None:
    """
    Regenerate app_data.json for the current machine using AppOpener.
    """
    AppOpener.mklist(name="app_data.json", path=SRC_DIR, output=False)


def load_camera_view_enabled(path: str = MAPPING_PATH) -> bool:
    """
    Load whether the live camera preview window should be shown.
    Defaults to False when key is missing.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return bool(data.get(CAMERA_VIEW_ENABLED_KEY, False))


def save_camera_view_enabled(enabled: bool, path: str = MAPPING_PATH) -> None:
    """
    Persist the camera preview visibility toggle.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data[CAMERA_VIEW_ENABLED_KEY] = bool(enabled)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_person_recognition_enabled(path: str = MAPPING_PATH) -> bool:
    """
    Load whether person recognition is enabled.
    Defaults to True when key is missing to preserve existing behavior.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return bool(data.get(PERSON_RECOGNITION_ENABLED_KEY, True))


def save_person_recognition_enabled(enabled: bool, path: str = MAPPING_PATH) -> None:
    """
    Persist the person-recognition toggle.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data[PERSON_RECOGNITION_ENABLED_KEY] = bool(enabled)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_dynamic_apps(path: str = MAPPING_PATH) -> list:
    """
    Load the ordered list of dynamically added app names from the mapping file.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get(DYNAMIC_APPS_KEY, []))

def load_run_uses_camera(path: str = MAPPING_PATH) -> bool:
    """
    Load the persisted camera-use flag for the run action row.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return bool(data.get(RUN_USES_CAMERA_KEY, False))

def load_game_run_path(path: str = MAPPING_PATH) -> str:
    """
    Load the persisted file path for a single run-game row (backward compat).
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return str(data.get(GAME_RUN_PATH_KEY, "")).strip()


def load_game_run_paths(path: str = MAPPING_PATH) -> list:
    """
    Load the list of persisted game file paths.
    Falls back to wrapping the old single-path key for backward compatibility.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if GAME_RUN_PATHS_KEY in data:
        return [str(p).strip() for p in data[GAME_RUN_PATHS_KEY] if str(p).strip()]
    old = str(data.get(GAME_RUN_PATH_KEY, "")).strip()
    return [old] if old else []


def load_file_run_entries(path: str = MAPPING_PATH) -> list:
    """
    Load the list of persisted file-run entries, each a dict with 'path' and 'uses_camera'.
    Returns an empty list when the key is absent (caller handles backward compat).
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        {"path": str(e.get("path", "")).strip(), "uses_camera": bool(e.get("uses_camera", False))}
        for e in data.get(FILE_RUN_ENTRIES_KEY, [])
        if str(e.get("path", "")).strip()
    ]


def save_mapping(
    mapping: dict,
    path: str = MAPPING_PATH,
    game_run_paths: list = None,
    file_run_entries: list = None,
    dynamic_apps: list = None,
    camera_view_enabled: bool = False,
    person_recognition_enabled: bool = True,
) -> None:
    """
    Persist the provided gesture-to-action mapping to JSON.
    """
    normalized_game_paths = [str(p).strip() for p in (game_run_paths or []) if str(p).strip()]

    out = {g: str(mapping.get(g, "")).strip() for g in SUPPORTED_GESTURES}
    out[DYNAMIC_APPS_KEY] = list(dynamic_apps) if dynamic_apps else []
    out[GAME_RUN_PATHS_KEY] = normalized_game_paths
    out[RUN_USES_CAMERA_KEY] = bool(normalized_game_paths)
    out[FILE_RUN_ENTRIES_KEY] = list(file_run_entries or [])
    out[CAMERA_VIEW_ENABLED_KEY] = bool(camera_view_enabled)
    out[PERSON_RECOGNITION_ENABLED_KEY] = bool(person_recognition_enabled)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
