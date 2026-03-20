from gui.actions import get_run_path, is_run_action


def build_action_to_gesture(mapping: dict) -> dict:
    """Invert gesture->action mapping into action->gesture for assigned entries."""
    return {action: gesture for gesture, action in mapping.items() if action}


def merged_dynamic_apps(saved_dynamic_apps: list, action_to_gesture: dict) -> list:
    """Return saved dynamic apps plus any open/close apps found in existing mappings."""
    dynamic_app_names = list(saved_dynamic_apps)
    mapped_open_close_apps = {
        action.split(":", 1)[1].strip()
        for action in action_to_gesture
        if action.startswith("open:") or action.startswith("close:")
    }
    for app_name in sorted(mapped_open_close_apps):
        if app_name and app_name not in dynamic_app_names:
            dynamic_app_names.append(app_name)
    return dynamic_app_names


def ensure_file_entries(
    file_entries: list,
    action_to_gesture: dict,
    no_gui_action: str,
    game_run_paths: list,
    fallback_run_uses_camera: bool,
    make_run_action,
) -> list:
    """Return file-run entries, reconstructing from legacy mapping keys when missing."""
    if file_entries:
        return file_entries

    excluded = {no_gui_action} | {make_run_action(path) for path in game_run_paths if path}
    old_run = next(
        (action for action in action_to_gesture if is_run_action(action) and action not in excluded),
        "",
    )
    if not old_run:
        return []

    return [{"path": get_run_path(old_run), "uses_camera": fallback_run_uses_camera}]
