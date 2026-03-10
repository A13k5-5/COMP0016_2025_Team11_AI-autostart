import os

from PySide6 import QtWidgets

from gui.actions import (
    SUPPORTED_GESTURES,
    SUPPORTED_ACTIONS,
    load_mapping,
    load_run_uses_camera,
    save_mapping,
    is_run_action,
    make_run_action,
    get_run_path,
)

class MappingWindow(QtWidgets.QWidget):
    """
    Window for configuring gesture-to-action mappings.

    Rows are split into three groups:
    - One row per entry in SUPPORTED_ACTIONS (predefined actions).
    - One extra "Select Game" row where the user can browse game files.
    - One extra "No GUI Game Engine" fixed row.

    The "Select Game" row index is always ``len(SUPPORTED_ACTIONS)``.
    """

    # Indexes of special rows appended after SUPPORTED_ACTIONS rows
    _RUN_ROW: int = len(SUPPORTED_ACTIONS)
    _NO_GUI_GAME_ENGINE_ROW: int = len(SUPPORTED_ACTIONS) + 1
    _TOTAL_ROWS: int = len(SUPPORTED_ACTIONS) + 2

    # Temporary test path
    _NO_GUI_GAME_ENGINE_RELATIVE_PATH = "gameEngine/gameEngine.exec"

    def __init__(self):
        super().__init__()
        self._setup_window("Customize the mapping between gestures and actions.", 620, 360)
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

    def _create_widgets(self) -> None:
        """
        Create all widgets used by the mapping editor.
        """
        self.table = QtWidgets.QTableWidget(self._TOTAL_ROWS, 2)
        self.table.setHorizontalHeaderLabels(["Action", "Gesture"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive) 
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch) 
        self.table.setColumnWidth(0, 280)

        self.reload_btn = QtWidgets.QPushButton("Discard Changes")
        self.clear_btn = QtWidgets.QPushButton("Clear Selections")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.status = QtWidgets.QLabel("")

        self.button_row = QtWidgets.QHBoxLayout()

    def _add_widgets(self) -> None:
        """
        Insert widgets into the main layout.
        """
        self.layout.addWidget(self.table)

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

    def _set_action_cell(self, row: int, action: str) -> None:
        """
        Set the action text in the left column (read-only).
        """
        action_item = QtWidgets.QTableWidgetItem(action)
        action_item.setFlags(action_item.flags() & ~QtWidgets.QTableWidgetItem().flags().ItemIsEditable)
        self.table.setItem(row, 0, action_item)

    def _set_gesture_cell(self, row: int, gesture: str) -> None:
        """
        Set a gesture dropdown for the provided row.
        """
        combo = self._create_gesture_combo(gesture)
        combo.currentTextChanged.connect(self._refresh_gesture_options)
        self.table.setCellWidget(row, 1, combo)

    def _set_run_row(self, exe_path: str = "", gesture: str = "", uses_camera: bool = False) -> None:
        """
        Populate the "Select Game" row with a path-picker widget and gesture
        dropdown.

        The action cell contains a horizontal sub-widget: a read-only label
        showing the chosen path and a "Browse…" button that opens a file dialog.
        """
        row = self._RUN_ROW

        # --- Action cell: label + browse button ---
        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(2, 2, 2, 2)

        path_label = QtWidgets.QLabel(exe_path or "No file selected")
        path_label.setToolTip(exe_path)
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.setFixedWidth(70)
        uses_camera_cb = QtWidgets.QCheckBox("Uses camera")
        uses_camera_cb.setChecked(uses_camera)

        h_layout.addWidget(path_label, stretch=1)
        h_layout.addWidget(browse_btn)
        h_layout.addWidget(uses_camera_cb)

        self.table.setCellWidget(row, 0, container)

        # Keep references so we can read/write the path later
        self._run_path_label = path_label
        self._run_browse_btn = browse_btn
        self._run_uses_camera_cb = uses_camera_cb

        browse_btn.clicked.connect(self._browse_game_file)

        # --- Gesture cell ---
        self._set_gesture_cell(row, gesture)

    def _project_root(self) -> str:
        return os.path.dirname(os.path.dirname(__file__))

    def _to_relative_project_path(self, path: str) -> str:
        rel_path = os.path.relpath(path, self._project_root())
        return rel_path.replace("\\", "/")

    def _browse_game_file(self) -> None:
        """
        Open a file dialog to choose any file; update path label using a relative path.
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*)",
        )
        if path:
            relative_path = self._to_relative_project_path(os.path.abspath(path))
            self._run_path_label.setText(relative_path)
            self._run_path_label.setToolTip(relative_path)

    def _set_no_gui_game_engine_row(self, gesture: str = "") -> None:
        """Populate the fixed No GUI Game Engine row and gesture dropdown."""
        row = self._NO_GUI_GAME_ENGINE_ROW

        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(2, 2, 2, 2)

        title_label = QtWidgets.QLabel("No GUI Game Engine")
        path_label = QtWidgets.QLabel(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)
        path_label.setToolTip(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)

        h_layout.addWidget(title_label)
        h_layout.addWidget(path_label, stretch=1)

        self.table.setCellWidget(row, 0, container)
        self._set_gesture_cell(row, gesture)

    def _get_run_exe_path(self) -> str:
        """Return the currently selected executable path, or empty string."""
        text = self._run_path_label.text().strip()
        return "" if text == "No file selected" else text

    def load_into_table(self) -> None:
        """
        Load mapping file and populate table rows.
        """
        mapping = load_mapping()
        action_to_gesture = {a: g for g, a in mapping.items() if a}

        # Predefined-action rows
        for row, action in enumerate(SUPPORTED_ACTIONS):
            self._set_action_cell(row, action)
            self._set_gesture_cell(row, action_to_gesture.get(action, ""))

        # Special rows based on existing run: entries
        no_gui_action = make_run_action(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)
        no_gui_gesture = action_to_gesture.get(no_gui_action, "")

        run_action = next(
            (a for a in action_to_gesture if is_run_action(a) and a != no_gui_action),
            "",
        )
        exe_path = get_run_path(run_action) if run_action else ""
        run_gesture = action_to_gesture.get(run_action, "")
        run_uses_camera = load_run_uses_camera()
        self._set_run_row(exe_path, run_gesture, run_uses_camera)
        self._set_no_gui_game_engine_row(no_gui_gesture)

        self._refresh_gesture_options()

        self.status.setText("Previous selections loaded from file.")

    def _refresh_gesture_options(self) -> None:
        """
        Keep each dropdown limited to gestures not already used in other rows.
        """
        combos = [self.table.cellWidget(row, 1) for row in range(self._TOTAL_ROWS)]
        selected = [combo.currentText().strip() for combo in combos if combo is not None]

        for combo in combos:
            if combo is None:
                continue

            current = combo.currentText().strip()
            used_by_others = {g for g in selected if g and g != current}
            available = ["None", *[g for g in SUPPORTED_GESTURES if g not in used_by_others]]

            # Block signals while mutating options to avoid recursive refresh calls.
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

        # Predefined-action rows
        for row, action in enumerate(SUPPORTED_ACTIONS):
            combo = self.table.cellWidget(row, 1)
            gesture = combo.currentText().strip()
            if gesture and gesture != "None":
                out[gesture] = action

        # Run-executable row
        exe_path = self._get_run_exe_path()
        run_combo = self.table.cellWidget(self._RUN_ROW, 1)
        run_gesture = run_combo.currentText().strip() if run_combo else ""
        if exe_path and run_gesture and run_gesture != "None":
            out[run_gesture] = make_run_action(exe_path)

        # No GUI Game Engine row (fixed executable)
        no_gui_combo = self.table.cellWidget(self._NO_GUI_GAME_ENGINE_ROW, 1)
        no_gui_gesture = no_gui_combo.currentText().strip() if no_gui_combo else ""
        if no_gui_gesture and no_gui_gesture != "None":
            out[no_gui_gesture] = make_run_action(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)

        return out

    def clear_selections(self) -> None:
        """
        Reset all gesture selections to blank without saving.
        """
        for row in range(self._TOTAL_ROWS):
            combo = self.table.cellWidget(row, 1)
            if combo is not None:
                combo.blockSignals(True)
                combo.setCurrentIndex(0)
                combo.blockSignals(False)

        # Also clear the executable path label
        self._run_path_label.setText("No file selected")
        self._run_path_label.setToolTip("")
        self._run_uses_camera_cb.setChecked(False)

        self._refresh_gesture_options()
        self.status.setText("Selections cleared.")

    def save_from_table(self) -> None:
        """
        Persist current table selections to the JSON mapping file.
        """
        out = self._collect_mapping_from_table()
        save_mapping(out, run_uses_camera=self._run_uses_camera_cb.isChecked())
        self.status.setText("Saved to file.")