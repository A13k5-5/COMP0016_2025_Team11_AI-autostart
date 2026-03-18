from PySide6 import QtCore, QtWidgets


def iter_gesture_combos(
    app_table: QtWidgets.QTableWidget,
    game_table: QtWidgets.QTableWidget,
    file_table: QtWidgets.QTableWidget,
):
    """Yield all gesture combo boxes across app, game, and file tables."""
    for row in range(app_table.rowCount()):
        combo = app_table.cellWidget(row, 1)
        if combo is not None:
            yield combo
    for row in range(game_table.rowCount()):
        combo = game_table.cellWidget(row, 1)
        if combo is not None:
            yield combo
    for row in range(file_table.rowCount()):
        combo = file_table.cellWidget(row, 2)
        if combo is not None:
            yield combo


def refresh_gesture_options(
    app_table: QtWidgets.QTableWidget,
    game_table: QtWidgets.QTableWidget,
    file_table: QtWidgets.QTableWidget,
    supported_gestures: list[str],
) -> None:
    """Limit each dropdown to gestures not already used in other rows."""
    combos = list(iter_gesture_combos(app_table, game_table, file_table))
    selected = [combo.currentText().strip() for combo in combos]

    for combo in combos:
        current = combo.currentText().strip()
        used_by_others = {gesture for gesture in selected if gesture and gesture != current}
        available = ["None", *[gesture for gesture in supported_gestures if gesture not in used_by_others]]

        combo.blockSignals(True)
        combo.clear()
        combo.addItems(available)
        idx = combo.findText(current)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)


def get_cell_path(table: QtWidgets.QTableWidget, row: int, col: int = 0) -> str:
    """Return the full path stored in a browse-row cell's path label tooltip."""
    container = table.cellWidget(row, col)
    if container is None:
        return ""
    labels = container.findChildren(QtWidgets.QLabel)
    return labels[0].toolTip() if labels else ""


def get_cell_uses_camera(table: QtWidgets.QTableWidget, row: int, col: int = 1) -> bool:
    """Return the uses-camera checkbox state from a file-row cell."""
    container = table.cellWidget(row, col)
    if container is None:
        return False
    cbs = container.findChildren(QtWidgets.QCheckBox)
    return cbs[0].isChecked() if cbs else False


def collect_mapping_from_tables(
    app_table: QtWidgets.QTableWidget,
    game_table: QtWidgets.QTableWidget,
    file_table: QtWidgets.QTableWidget,
    supported_gestures: list[str],
    game_engine_row: int,
    no_gui_game_engine_relative_path: str,
    make_run_action,
) -> dict:
    """Collect current dropdown selections into a gesture-to-action mapping."""
    out = {gesture: "" for gesture in supported_gestures}

    for row in range(app_table.rowCount()):
        action_item = app_table.item(row, 0)
        action = action_item.data(QtCore.Qt.UserRole) if action_item else ""
        action = str(action).strip() if action else ""
        combo = app_table.cellWidget(row, 1)
        gesture = combo.currentText().strip() if combo else ""
        if action and gesture and gesture != "None":
            out[gesture] = action

    no_gui_combo = game_table.cellWidget(game_engine_row, 1)
    no_gui_gesture = no_gui_combo.currentText().strip() if no_gui_combo else ""
    if no_gui_gesture and no_gui_gesture != "None":
        out[no_gui_gesture] = make_run_action(no_gui_game_engine_relative_path)

    for row in range(game_engine_row + 1, game_table.rowCount()):
        path = get_cell_path(game_table, row)
        combo = game_table.cellWidget(row, 1)
        gesture = combo.currentText().strip() if combo else ""
        if path and gesture and gesture != "None":
            out[gesture] = make_run_action(path)

    for row in range(file_table.rowCount()):
        path = get_cell_path(file_table, row)
        combo = file_table.cellWidget(row, 2)
        gesture = combo.currentText().strip() if combo else ""
        if path and gesture and gesture != "None":
            out[gesture] = make_run_action(path)

    return out


def collect_dynamic_apps(app_table: QtWidgets.QTableWidget, static_rows: int) -> list[str]:
    """Collect ordered dynamic app names from app table action rows."""
    dynamic_apps: list[str] = []
    seen: set[str] = set()
    for row in range(static_rows, app_table.rowCount()):
        action_item = app_table.item(row, 0)
        if action_item is None:
            continue

        action = action_item.data(QtCore.Qt.UserRole)
        action = str(action).strip() if action else ""
        for prefix in ("open:", "close:"):
            if action.startswith(prefix):
                name = action[len(prefix):]
                if name not in seen:
                    seen.add(name)
                    dynamic_apps.append(name)
                break

    return dynamic_apps


def collect_game_run_paths(game_table: QtWidgets.QTableWidget, start_row: int = 1) -> list[str]:
    """Collect ordered game run paths from game table dynamic rows."""
    return [
        get_cell_path(game_table, row)
        for row in range(start_row, game_table.rowCount())
        if get_cell_path(game_table, row)
    ]


def collect_file_run_entries(file_table: QtWidgets.QTableWidget) -> list[dict]:
    """Collect file run entries (path + uses_camera) from file table rows."""
    return [
        {
            "path": get_cell_path(file_table, row),
            "uses_camera": get_cell_uses_camera(file_table, row),
        }
        for row in range(file_table.rowCount())
        if get_cell_path(file_table, row)
    ]
