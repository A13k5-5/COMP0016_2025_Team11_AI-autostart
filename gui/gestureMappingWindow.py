import os

from PySide6 import QtWidgets

from gui.actions import (
    SUPPORTED_GESTURES,
    SUPPORTED_ACTIONS,
    load_mapping,
    load_run_uses_camera,
    load_game_run_path,
    load_app_data,
    load_dynamic_apps,
    save_mapping,
    is_run_action,
    make_run_action,
    get_run_path,
)


class AddAppDialog(QtWidgets.QDialog):
    """
    Modal popup that lets the user pick an app from app_data.json.
    Returns the selected app name (lowercase key) via selected_app().
    """

    def __init__(self, app_names: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add App")
        self.resize(380, 480)

        layout = QtWidgets.QVBoxLayout(self)

        self._search = QtWidgets.QLineEdit()
        self._search.setPlaceholderText("Search apps…")
        layout.addWidget(self._search)

        self._list = QtWidgets.QListWidget()
        self._all_names = sorted(app_names)
        self._list.addItems(self._all_names)
        layout.addWidget(self._list)

        btn_row = QtWidgets.QHBoxLayout()
        self._add_btn = QtWidgets.QPushButton("Add")
        self._add_btn.setEnabled(False)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self._search.textChanged.connect(self._filter)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(lambda _: self.accept())
        self._add_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def _filter(self, text: str) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _on_selection_changed(self) -> None:
        self._add_btn.setEnabled(bool(self._list.selectedItems()))

    def selected_app(self) -> str:
        items = self._list.selectedItems()
        return items[0].text() if items else ""

class MappingWindow(QtWidgets.QWidget):
    """
    Window for configuring gesture-to-action mappings.

    A navigation bar at the top switches between four pages via a QStackedWidget:
      - App Actions:      one row per SUPPORTED_ACTIONS entry + dynamic app rows.
      - Game Actions:     No GUI Game Engine row + run-game row.
      - File Opening:     run-file row with Uses Camera toggle.
      - Gesture Reference: read-only display of fixed/reserved gesture assignments.

    Save / Discard / Clear buttons sit in a fixed bar at the bottom of the window,
    always visible regardless of the active page.
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
        self.layout.setSpacing(4)

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
        # --- Nav buttons ---
        self._nav_buttons: list[QtWidgets.QPushButton] = []
        for label in ("App Actions", "Game Actions", "File Opening", "Gesture Reference"):
            btn = QtWidgets.QPushButton(label)
            btn.setFlat(True)
            self._nav_buttons.append(btn)

        # --- Stacked widget ---
        self._stack = QtWidgets.QStackedWidget()

        # Page 0 – App Actions
        self._page_apps = QtWidgets.QWidget()
        apps_layout = QtWidgets.QVBoxLayout(self._page_apps)
        self.app_table = QtWidgets.QTableWidget(self._APP_TABLE_ROWS, 2)
        self._init_table(self.app_table)
        self._add_app_btn = QtWidgets.QPushButton("+ Add App")
        apps_layout.addWidget(self.app_table)
        apps_layout.addWidget(self._add_app_btn)

        # Page 1 – Game Actions
        self._page_games = QtWidgets.QWidget()
        games_layout = QtWidgets.QVBoxLayout(self._page_games)
        self.game_table = QtWidgets.QTableWidget(self._GAME_TABLE_ROWS, 2)
        self._init_table(self.game_table)
        games_layout.addWidget(self.game_table)

        # Page 2 – File Opening
        self._page_files = QtWidgets.QWidget()
        files_layout = QtWidgets.QVBoxLayout(self._page_files)
        self.file_table = QtWidgets.QTableWidget(self._FILE_TABLE_ROWS, 3)
        self.file_table.setHorizontalHeaderLabels(["Action", "Uses Camera", "Gesture"])
        file_header = self.file_table.horizontalHeader()
        file_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        file_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        file_header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.file_table.setColumnWidth(0, 280)
        self.file_table.setColumnWidth(1, 100)
        files_layout.addWidget(self.file_table)

        # Page 3 – Gesture Reference (read-only)
        self._page_reference = QtWidgets.QWidget()
        ref_layout = QtWidgets.QVBoxLayout(self._page_reference)
        ref_layout.addWidget(QtWidgets.QLabel("These gesture assignments are fixed and cannot be changed."))
        info_table = QtWidgets.QTableWidget(1, 2)
        info_table.setHorizontalHeaderLabels(["Action", "Gesture"])
        info_header = info_table.horizontalHeader()
        info_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        info_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        info_table.setColumnWidth(0, 280)
        info_table.verticalHeader().hide()
        info_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        info_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        info_table.setFixedHeight(
            info_table.rowHeight(0) + info_table.horizontalHeader().height() + 4
        )
        info_table.setItem(0, 0, QtWidgets.QTableWidgetItem("Deactivate Low Power Mode"))
        info_table.setItem(0, 1, QtWidgets.QTableWidgetItem("Open_Palm (hold 2 s)"))
        ref_layout.addWidget(info_table)
        ref_layout.addStretch()

        for page in (self._page_apps, self._page_games, self._page_files, self._page_reference):
            self._stack.addWidget(page)

        # --- Shared bottom controls ---
        self.reload_btn = QtWidgets.QPushButton("Discard Changes")
        self.clear_btn = QtWidgets.QPushButton("Clear Selections")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.status = QtWidgets.QLabel("")
        self.button_row = QtWidgets.QHBoxLayout()

    def _add_widgets(self) -> None:
        """
        Insert nav bar, stacked pages, and shared bottom controls into the main layout.
        """
        # Navigation bar
        nav_bar = QtWidgets.QHBoxLayout()
        nav_bar.setSpacing(0)
        for btn in self._nav_buttons:
            nav_bar.addWidget(btn)
        nav_bar.addStretch()
        self.layout.addLayout(nav_bar)

        # Divider line
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.layout.addWidget(line)

        # Stacked content area
        self.layout.addWidget(self._stack, stretch=1)

        # Bottom controls (always visible)
        self.button_row.addWidget(self.reload_btn)
        self.button_row.addWidget(self.clear_btn)
        self.button_row.addWidget(self.save_btn)
        self.layout.addLayout(self.button_row)
        self.layout.addWidget(self.status)

    def _connect_signals(self) -> None:
        """
        Connect button actions and nav bar to their handlers.
        """
        self.reload_btn.clicked.connect(self.load_into_table)
        self.clear_btn.clicked.connect(self.clear_selections)
        self.save_btn.clicked.connect(self.save_from_table)
        self._add_app_btn.clicked.connect(self._open_add_app_dialog)
        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
        self._navigate(0)  # start on App Actions

    def _navigate(self, index: int) -> None:
        """Switch to the page at *index* and mark the active nav button bold."""
        self._stack.setCurrentIndex(index)
        # Hide Save/Clear/Discard on the read-only Gesture Reference page
        reference_page = 3
        for w in (self.reload_btn, self.clear_btn, self.save_btn):
            w.setVisible(index != reference_page)
        for i, btn in enumerate(self._nav_buttons):
            font = btn.font()
            font.setBold(i == index)
            btn.setFont(font)
            btn.setFlat(i != index)

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

    def _clear_dynamic_app_rows(self) -> None:
        """Remove all rows that were added dynamically beyond the static ones."""
        while self.app_table.rowCount() > self._APP_TABLE_ROWS:
            self.app_table.removeRow(self.app_table.rowCount() - 1)

    def _add_app_row(self, app_name: str, open_gesture: str = "", close_gesture: str = "") -> None:
        """Append open and close rows for *app_name* to the app table."""
        for prefix, gesture in (("open", open_gesture), ("close", close_gesture)):
            row = self.app_table.rowCount()
            self.app_table.insertRow(row)
            self._set_action_cell(self.app_table, row, f"{prefix}:{app_name}")
            self._set_gesture_cell(self.app_table, row, gesture)
        self._refresh_gesture_options()

    def _open_add_app_dialog(self) -> None:
        """Show the app picker popup and add the chosen app's rows."""
        app_names = list(load_app_data().keys())
        dlg = AddAppDialog(app_names, parent=self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            app_name = dlg.selected_app()
            if app_name:
                self._add_app_row(app_name)

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
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Game File", "", "No UI Files (*.noui)")
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
        for row in range(self.app_table.rowCount()):  # includes dynamic rows
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

        # Dynamic app rows — restore from saved list
        self._clear_dynamic_app_rows()
        for app_name in load_dynamic_apps():
            open_action = f"open:{app_name}"
            close_action = f"close:{app_name}"
            self._add_app_row(
                app_name,
                open_gesture=action_to_gesture.get(open_action, ""),
                close_gesture=action_to_gesture.get(close_action, ""),
            )

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

        # App table (static + dynamic rows)
        for row in range(self.app_table.rowCount()):
            action_item = self.app_table.item(row, 0)
            action = action_item.text().strip() if action_item else ""
            combo = self.app_table.cellWidget(row, 1)
            gesture = combo.currentText().strip() if combo else ""
            if action and gesture and gesture != "None":
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

        # Collect ordered list of dynamic app names
        dynamic_apps = []
        seen: set = set()
        for row in range(self._APP_TABLE_ROWS, self.app_table.rowCount()):
            action_item = self.app_table.item(row, 0)
            if action_item:
                action = action_item.text().strip()
                for prefix in ("open:", "close:"):
                    if action.startswith(prefix):
                        name = action[len(prefix):]
                        if name not in seen:
                            seen.add(name)
                            dynamic_apps.append(name)
                        break

        save_mapping(
            out,
            run_uses_camera=self._run_uses_camera_cb.isChecked(),
            game_run_path=self._get_run_game_exe_path(),
            dynamic_apps=dynamic_apps,
        )
        self.status.setText("Saved to file.")