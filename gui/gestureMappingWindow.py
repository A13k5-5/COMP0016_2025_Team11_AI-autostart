import os

from PySide6 import QtWidgets

from gui.actions import (
    SUPPORTED_GESTURES,
    SUPPORTED_ACTIONS,
    load_mapping,
    load_run_uses_camera,
    load_game_run_path,
    save_mapping,
    is_run_action,
    make_run_action,
    get_run_path,
)

class MappingWindow(QtWidgets.QWidget):
    """
    Window for configuring gesture-to-action mappings.

    Layout:
    - App table:          one row per SUPPORTED_ACTIONS entry.
    - Game table:         No GUI Game Engine row (fixed path) + run-game row
                          (always uses camera; no toggle shown).
    - File opening table: run-file row with Uses Camera toggle.
    - Info row:           read-only display of the reserved Open Palm gesture.
    """

    # App table
    _APP_TABLE_ROWS: int = len(SUPPORTED_ACTIONS)

    # Game table row indices
    _GAME_ENGINE_ROW: int = 0
    _RUN_GAME_ROW: int = 1
    _GAME_TABLE_ROWS: int = 2

    # File opening table row indices
    _FILE_RUN_ROW: int = 0
    _FILE_TABLE_ROWS: int = 1

    _NO_GUI_GAME_ENGINE_RELATIVE_PATH = "gameEngine/gameEngine.exec"

    def __init__(self):
        super().__init__()
        self._setup_window("Customize the mapping between gestures and actions.", 620, 520)
        self._create_widgets()
        self._add_widgets()
        self._connect_signals()
        self.load_into_table()

    def _setup_window(self, title: str, width: int, height: int) -> None:
        """
        Configure window title, size, and root layout.
        """
        self.setWindowTitle(title)
        self.resize(width, height)
        self.layout = QtWidgets.QVBoxLayout(self)

    def _init_table(self, table: QtWidgets.QTableWidget) -> None:
        """Apply shared column/header settings to a table."""
        table.setHorizontalHeaderLabels(["Action", "Gesture"])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        table.setColumnWidth(0, 280)

    def _create_widgets(self) -> None:
        """
        Create all widgets used by the mapping editor.
        """
        self.app_table = QtWidgets.QTableWidget(self._APP_TABLE_ROWS, 2)
        self._init_table(self.app_table)

        self.game_table = QtWidgets.QTableWidget(self._GAME_TABLE_ROWS, 2)
        self._init_table(self.game_table)

        self.file_table = QtWidgets.QTableWidget(self._FILE_TABLE_ROWS, 3)
        self.file_table.setHorizontalHeaderLabels(["Action", "Uses Camera", "Gesture"])
        file_header = self.file_table.horizontalHeader()
        file_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        file_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        file_header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.file_table.setColumnWidth(0, 280)
        self.file_table.setColumnWidth(1, 100)

        self.reload_btn = QtWidgets.QPushButton("Discard Changes")
        self.clear_btn = QtWidgets.QPushButton("Clear Selections")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.status = QtWidgets.QLabel("")

        self.button_row = QtWidgets.QHBoxLayout()

    def _add_widgets(self) -> None:
        """
        Insert widgets into the main layout.
        """
        self.layout.addWidget(QtWidgets.QLabel("App Actions"))
        self.layout.addWidget(self.app_table)

        self.layout.addWidget(QtWidgets.QLabel("Game Actions"))
        self.layout.addWidget(self.game_table)

        self.layout.addWidget(QtWidgets.QLabel("File Opening Actions"))
        self.layout.addWidget(self.file_table)

        self.layout.addWidget(QtWidgets.QLabel("Fixed Settings"))

        # Read-only row showing the reserved Open Palm gesture
        info_table = QtWidgets.QTableWidget(1, 2)
        info_table.horizontalHeader().hide()
        info_table.verticalHeader().hide()
        info_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        info_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        info_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        info_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        info_table.setColumnWidth(0, 280)
        info_table.setFixedHeight(info_table.rowHeight(0) + 4)
        info_table.setItem(0, 0, QtWidgets.QTableWidgetItem("Deactivate Low Power Mode"))
        info_table.setItem(0, 1, QtWidgets.QTableWidgetItem("Open_Palm"))
        self.layout.addWidget(info_table)

        self.button_row.addWidget(self.reload_btn)
        self.button_row.addWidget(self.clear_btn)
        self.button_row.addWidget(self.save_btn)
        self.layout.addLayout(self.button_row)

        self.layout.addWidget(self.status)

    def _connect_signals(self) -> None:
        """
        Connect button actions to their handlers.
        """
        self.reload_btn.clicked.connect(self.load_into_table)
        self.clear_btn.clicked.connect(self.clear_selections)
        self.save_btn.clicked.connect(self.save_from_table)

    def _create_gesture_combo(self, current_gesture: str) -> QtWidgets.QComboBox:
        """
        Create a gesture dropdown with a blank option and pre-selected value.
        """
        combo = QtWidgets.QComboBox()
        combo.addItem("None")
        combo.addItems(SUPPORTED_GESTURES)
        idx = combo.findText(current_gesture)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        return combo

    def _set_action_cell(self, table: QtWidgets.QTableWidget, row: int, action: str) -> None:
        """
        Set the action text in the left column (read-only).
        """
        action_item = QtWidgets.QTableWidgetItem(action)
        action_item.setFlags(action_item.flags() & ~QtWidgets.QTableWidgetItem().flags().ItemIsEditable)
        table.setItem(row, 0, action_item)

    def _set_gesture_cell(self, table: QtWidgets.QTableWidget, row: int, gesture: str, col: int = 1) -> None:
        """
        Set a gesture dropdown for the provided row.
        """
        combo = self._create_gesture_combo(gesture)
        combo.currentTextChanged.connect(self._refresh_gesture_options)
        table.setCellWidget(row, col, combo)

    def _project_root(self) -> str:
        return os.path.dirname(os.path.dirname(__file__))

    def _to_relative_project_path(self, path: str) -> str:
        return os.path.relpath(path, self._project_root()).replace("\\", "/")

    def _set_no_gui_game_engine_row(self, gesture: str = "") -> None:
        """Populate the fixed No GUI Game Engine row in the game table."""
        self._set_action_cell(self.game_table, self._GAME_ENGINE_ROW, "No GUI Game Engine")
        self._set_gesture_cell(self.game_table, self._GAME_ENGINE_ROW, gesture, col=1)

    def _set_run_row(self, exe_path: str = "", gesture: str = "", uses_camera: bool = False) -> None:
        """Populate the run-file row in the file opening table."""
        self._run_full_path = exe_path

        # Col 0: filename label + browse button
        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(2, 2, 2, 2)
        display_name = os.path.basename(exe_path) if exe_path else "No file selected"
        self._run_path_label = QtWidgets.QLabel(display_name)
        self._run_path_label.setToolTip(exe_path)
        self._run_browse_btn = QtWidgets.QPushButton("Browse…")
        self._run_browse_btn.setFixedWidth(70)
        h_layout.addWidget(self._run_path_label, stretch=1)
        h_layout.addWidget(self._run_browse_btn)
        self.file_table.setCellWidget(self._FILE_RUN_ROW, 0, container)
        self._run_browse_btn.clicked.connect(self._browse_run_file)

        # Col 1: uses camera checkbox (centred)
        cb_container = QtWidgets.QWidget()
        cb_layout = QtWidgets.QHBoxLayout(cb_container)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.addStretch()
        self._run_uses_camera_cb = QtWidgets.QCheckBox()
        self._run_uses_camera_cb.setChecked(uses_camera)
        cb_layout.addWidget(self._run_uses_camera_cb)
        cb_layout.addStretch()
        self.file_table.setCellWidget(self._FILE_RUN_ROW, 1, cb_container)

        # Col 2: gesture dropdown
        self._set_gesture_cell(self.file_table, self._FILE_RUN_ROW, gesture, col=2)

    def _set_run_game_row(self, exe_path: str = "", gesture: str = "") -> None:
        """Populate the run-game row in the game table (always uses camera)."""
        self._run_game_full_path = exe_path

        # Col 0: filename label + browse button
        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(2, 2, 2, 2)
        display_name = os.path.basename(exe_path) if exe_path else "No file selected"
        self._run_game_path_label = QtWidgets.QLabel(display_name)
        self._run_game_path_label.setToolTip(exe_path)
        self._run_game_browse_btn = QtWidgets.QPushButton("Browse…")
        self._run_game_browse_btn.setFixedWidth(70)
        h_layout.addWidget(self._run_game_path_label, stretch=1)
        h_layout.addWidget(self._run_game_browse_btn)
        self.game_table.setCellWidget(self._RUN_GAME_ROW, 0, container)
        self._run_game_browse_btn.clicked.connect(self._browse_run_game_file)

        # Col 1: gesture dropdown
        self._set_gesture_cell(self.game_table, self._RUN_GAME_ROW, gesture, col=1)

    def _browse_run_file(self) -> None:
        """Open a file dialog to choose any file; store relative path, display filename only."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if path:
            self._run_full_path = self._to_relative_project_path(os.path.abspath(path))
            self._run_path_label.setText(os.path.basename(path))
            self._run_path_label.setToolTip(self._run_full_path)

    def _browse_run_game_file(self) -> None:
        """Open a file dialog to choose a game file; store relative path, display filename only."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Game File", "", "All Files (*)")
        if path:
            self._run_game_full_path = self._to_relative_project_path(os.path.abspath(path))
            self._run_game_path_label.setText(os.path.basename(path))
            self._run_game_path_label.setToolTip(self._run_game_full_path)

    def _get_run_exe_path(self) -> str:
        """Return the currently selected run file path, or empty string."""
        return self._run_full_path

    def _get_run_game_exe_path(self) -> str:
        """Return the currently selected run game path, or empty string."""
        return self._run_game_full_path

    def _all_combos(self):
        """Yield all gesture combos from all tables."""
        for row in range(self._APP_TABLE_ROWS):
            combo = self.app_table.cellWidget(row, 1)
            if combo is not None:
                yield combo
        for row in range(self._GAME_TABLE_ROWS):
            combo = self.game_table.cellWidget(row, 1)
            if combo is not None:
                yield combo
        for row in range(self._FILE_TABLE_ROWS):
            combo = self.file_table.cellWidget(row, 2)
            if combo is not None:
                yield combo

    def load_into_table(self) -> None:
        """
        Load mapping file and populate both tables.
        """
        mapping = load_mapping()
        action_to_gesture = {a: g for g, a in mapping.items() if a}

        # App table
        for row, action in enumerate(SUPPORTED_ACTIONS):
            self._set_action_cell(self.app_table, row, action)
            self._set_gesture_cell(self.app_table, row, action_to_gesture.get(action, ""))

        # Game table
        no_gui_action = make_run_action(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)
        no_gui_gesture = action_to_gesture.get(no_gui_action, "")
        self._set_no_gui_game_engine_row(no_gui_gesture)

        game_run_path = load_game_run_path()
        game_run_action = make_run_action(game_run_path) if game_run_path else ""
        game_run_gesture = action_to_gesture.get(game_run_action, "") if game_run_action else ""
        self._set_run_game_row(game_run_path, game_run_gesture)

        # File opening table
        run_action = next(
            (a for a in action_to_gesture if is_run_action(a) and a != no_gui_action and a != game_run_action), ""
        )
        exe_path = get_run_path(run_action) if run_action else ""
        run_gesture = action_to_gesture.get(run_action, "")
        run_uses_camera = load_run_uses_camera()
        self._set_run_row(exe_path, run_gesture, run_uses_camera)

        self._refresh_gesture_options()
        self.status.setText("Previous selections loaded from file.")

    def _refresh_gesture_options(self) -> None:
        """
        Keep each dropdown limited to gestures not already used in other rows.
        """
        combos = list(self._all_combos())
        selected = [c.currentText().strip() for c in combos]

        for combo in combos:
            current = combo.currentText().strip()
            used_by_others = {g for g in selected if g and g != current}
            available = ["None", *[g for g in SUPPORTED_GESTURES if g not in used_by_others]]

            combo.blockSignals(True)
            combo.clear()
            combo.addItems(available)
            idx = combo.findText(current)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            combo.blockSignals(False)

    def _collect_mapping_from_table(self) -> dict:
        """
        Collect current dropdown selections into a gesture-to-action mapping.
        """
        out = {g: "" for g in SUPPORTED_GESTURES}

        # App table
        for row, action in enumerate(SUPPORTED_ACTIONS):
            combo = self.app_table.cellWidget(row, 1)
            gesture = combo.currentText().strip()
            if gesture and gesture != "None":
                out[gesture] = action

        # Game table — No GUI Game Engine row
        no_gui_combo = self.game_table.cellWidget(self._GAME_ENGINE_ROW, 1)
        no_gui_gesture = no_gui_combo.currentText().strip() if no_gui_combo else ""
        if no_gui_gesture and no_gui_gesture != "None":
            out[no_gui_gesture] = make_run_action(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)

        # Game table — run-game row (always uses camera)
        game_exe_path = self._get_run_game_exe_path()
        run_game_combo = self.game_table.cellWidget(self._RUN_GAME_ROW, 1)
        run_game_gesture = run_game_combo.currentText().strip() if run_game_combo else ""
        if game_exe_path and run_game_gesture and run_game_gesture != "None":
            out[run_game_gesture] = make_run_action(game_exe_path)

        # File opening table — run-file row
        exe_path = self._get_run_exe_path()
        run_combo = self.file_table.cellWidget(self._FILE_RUN_ROW, 2)
        run_gesture = run_combo.currentText().strip() if run_combo else ""
        if exe_path and run_gesture and run_gesture != "None":
            out[run_gesture] = make_run_action(exe_path)

        return out

    def clear_selections(self) -> None:
        """
        Reset all gesture selections to blank without saving.
        """
        for combo in self._all_combos():
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

        self._run_full_path = ""
        self._run_path_label.setText("No file selected")
        self._run_path_label.setToolTip("")
        self._run_uses_camera_cb.setChecked(False)

        self._run_game_full_path = ""
        self._run_game_path_label.setText("No file selected")
        self._run_game_path_label.setToolTip("")

        self._refresh_gesture_options()
        self.status.setText("Selections cleared.")

    def save_from_table(self) -> None:
        """
        Persist current table selections to the JSON mapping file.
        """
        out = self._collect_mapping_from_table()
        save_mapping(
            out,
            run_uses_camera=self._run_uses_camera_cb.isChecked(),
            game_run_path=self._get_run_game_exe_path(),
        )
        self.status.setText("Saved to file.")