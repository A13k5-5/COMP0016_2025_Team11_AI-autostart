import os

from PySide6 import QtWidgets, QtGui, QtCore

from gui.actions import (
    SUPPORTED_GESTURES,
    SUPPORTED_ACTIONS,
    load_mapping,
    load_run_uses_camera,
    load_game_run_paths,
    load_file_run_entries,
    load_app_data,
    update_app_data,
    load_dynamic_apps,
    load_camera_view_enabled,
    save_camera_view_enabled,
    save_mapping,
    is_run_action,
    make_run_action,
    get_run_path,
)

from gui.AppDialog import AppDialog

# (gesture_key, icon_filename, display_name, icons8_attribution_url)
_GESTURE_ICONS: list[tuple[str, str, str, str]] = [
    ("Pointing_Up", "icons8-index-pointing-up-48.png", "Pointing Up", "icons8.com/icon/A8CsBXRU88Wm/index-pointing-up"),
    ("Closed_Fist", "icons8-raised-fist-48.png",       "Closed Fist", "icons8.com/icon/VkJPr-zo0ySl/raised-fist"),
    ("Victory",     "icons8-victory-hand-48.png",      "Victory",     "icons8.com/icon/T4rG9LrLu-OM/victory-hand"),
    ("ILoveYou",   "icons8-love-you-gesture-48.png",  "I Love You",  "icons8.com/icon/TLeK5N44Q2jW/love-you-gesture"),
    ("Thumb_Up",   "icons8-thumbs-up-48.png",         "Thumb Up",    "icons8.com/icon/FYJ9HNSqf_uK/thumbs-up"),
    ("Thumb_Down", "icons8-thumbs-down-48.png",       "Thumb Down",  "icons8.com/icon/cPJTvqEzTYvb/thumbs-down"),
    ("Open_Palm",  "icons8-raised-hand-48.png",       "Open Palm",   "icons8.com/icon/ykfYYMYPhA8j/raised-hand"),
]


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

    # Game table: only the No GUI Game Engine row is static; game-run rows are dynamic
    _GAME_ENGINE_ROW: int = 0
    # File table: all rows are dynamic

    _NO_GUI_GAME_ENGINE_RELATIVE_PATH = "gameEngine/gameEngine.exec"

    def __init__(self):
        super().__init__()
        self._setup_window("AI-Autostart settings", 620, 520)
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
        """Create all widgets used by the mapping editor."""
        # --- Nav buttons ---
        self._nav_buttons: list[QtWidgets.QPushButton] = []
        for label in ("App Actions", "Game Actions", "File Opening", "Gesture Reference"):
            btn = QtWidgets.QPushButton(label)
            btn.setFlat(True)
            self._nav_buttons.append(btn)

        # --- Stacked widget ---
        self._stack = QtWidgets.QStackedWidget()
        for page in (
            self._build_apps_page(),
            self._build_games_page(),
            self._build_files_page(),
            self._build_reference_page(),
        ):
            self._stack.addWidget(page)

        # --- Shared bottom controls ---
        self.reload_btn = QtWidgets.QPushButton("Discard Changes")
        self.clear_btn = QtWidgets.QPushButton("Clear Selections")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.status = QtWidgets.QLabel("")
        self.button_row = QtWidgets.QHBoxLayout()

    def _build_apps_page(self) -> QtWidgets.QWidget:
        """Build and return the App Actions page."""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        self.app_table = QtWidgets.QTableWidget(self._APP_TABLE_ROWS, 2)
        self._init_table(self.app_table)
        self._add_app_btn = QtWidgets.QPushButton("+ Add App")
        self._update_app_list_btn = QtWidgets.QPushButton("Update App List")
        self._delete_app_row_btn = QtWidgets.QPushButton("Delete Selected Row")
        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self._add_app_btn)
        button_row.addWidget(self._update_app_list_btn)
        button_row.addWidget(self._delete_app_row_btn)
        button_row.addStretch()
        layout.addWidget(self.app_table)
        layout.addLayout(button_row)
        return page

    def _build_games_page(self) -> QtWidgets.QWidget:
        """Build and return the Game Actions page."""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        self.game_table = QtWidgets.QTableWidget(1, 2)  # starts with only the engine row
        self._init_table(self.game_table)
        self._add_game_btn = QtWidgets.QPushButton("+ Add Game")
        layout.addWidget(self.game_table)
        layout.addWidget(self._add_game_btn)
        return page

    def _build_files_page(self) -> QtWidgets.QWidget:
        """Build and return the File Opening page."""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        self.file_table = QtWidgets.QTableWidget(0, 3)  # starts empty; all rows are dynamic
        self.file_table.setHorizontalHeaderLabels(["Action", "Uses Camera", "Gesture"])
        file_header = self.file_table.horizontalHeader()
        file_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        file_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        file_header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.file_table.setColumnWidth(0, 280)
        self.file_table.setColumnWidth(1, 100)
        self._add_file_btn = QtWidgets.QPushButton("+ Add File")
        layout.addWidget(self.file_table)
        layout.addWidget(self._add_file_btn)
        return page

    def _build_reference_page(self) -> QtWidgets.QWidget:
        """Build and return the Gesture Reference page."""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(10)

        display_title = QtWidgets.QLabel("Display Settings")
        font = display_title.font()
        font.setBold(True)
        display_title.setFont(font)
        layout.addWidget(display_title)
        self._camera_view_toggle = QtWidgets.QCheckBox("Show Camera View")
        self._camera_view_toggle.setChecked(False)
        layout.addWidget(self._camera_view_toggle)

        section_line_1 = QtWidgets.QFrame()
        section_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        section_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(section_line_1)

        fixed_title = QtWidgets.QLabel("Fixed Assignments")
        fixed_title.setFont(font)
        layout.addWidget(fixed_title)

        # Fixed assignments table
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
        layout.addWidget(info_table)

        section_line_2 = QtWidgets.QFrame()
        section_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        section_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(section_line_2)

        guide_title = QtWidgets.QLabel("Gesture Guide")
        guide_title.setFont(font)
        layout.addWidget(guide_title)

        # Gesture icon grid
        layout.addWidget(QtWidgets.QLabel("Available gestures:"))

        _ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        grid_widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(grid_widget)
        grid.setSpacing(16)
        grid.setContentsMargins(8, 8, 8, 8)

        COLS = 4
        for idx, (gesture, icon_file, display_name, attribution) in enumerate(_GESTURE_ICONS):
            cell = QtWidgets.QWidget()
            cell_layout = QtWidgets.QVBoxLayout(cell)
            cell_layout.setAlignment(QtCore.Qt.AlignCenter)
            cell_layout.setSpacing(4)

            icon_label = QtWidgets.QLabel()
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            icon_label.setToolTip(f"Icon by Icons8 — {attribution}")
            icon_path = os.path.join(_ICONS_DIR, icon_file)
            pixmap = QtGui.QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(
                    64, 64,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                ))
            else:
                icon_label.setText("[?]")

            name_label = QtWidgets.QLabel(display_name)
            name_label.setAlignment(QtCore.Qt.AlignCenter)

            cell_layout.addWidget(icon_label)
            cell_layout.addWidget(name_label)
            grid.addWidget(cell, idx // COLS, idx % COLS)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll, stretch=1)
        return page

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
        self._update_app_list_btn.clicked.connect(self._refresh_app_list)
        self._delete_app_row_btn.clicked.connect(self._delete_selected_app_rows)
        self._camera_view_toggle.toggled.connect(self._save_camera_view_setting)
        self._add_game_btn.clicked.connect(lambda: self._add_game_row())
        self._add_file_btn.clicked.connect(lambda: self._add_file_row())
        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
        self._navigate(0)  # start on App Actions

    def _delete_selected_app_rows(self) -> None:
        """Delete selected dynamic rows from the App Actions table."""
        selection_model = self.app_table.selectionModel()
        selected_rows = sorted(
            {
                index.row()
                for index in selection_model.selectedIndexes()
                if index.column() == 0
            },
            reverse=True,
        )
        if not selected_rows:
            self.status.setText("Select the action cell in column 1 to delete row(s).")
            return

        dynamic_rows = [row for row in selected_rows if row >= self._APP_TABLE_ROWS]
        if not dynamic_rows:
            self.status.setText("Built-in app rows cannot be deleted.")
            return

        for row in dynamic_rows:
            self.app_table.removeRow(row)

        self._refresh_gesture_options()
        self.status.setText("Selected row(s) deleted.")

    def _refresh_app_list(self) -> None:
        """Regenerate app_data.json from currently installed apps."""
        try:
            update_app_data()
            self.status.setText("App list updated.")
        except Exception as exc:
            self.status.setText(f"Failed to update app list: {exc}")

    def _save_camera_view_setting(self, enabled: bool) -> None:
        """Persist the camera-view toggle immediately from Gesture Reference page."""
        try:
            save_camera_view_enabled(enabled)
        except Exception as exc:
            self.status.setText(f"Failed to save camera view setting: {exc}")

    def _navigate(self, index: int) -> None:
        """Switch to the page at *index* and mark the active nav button bold."""
        self._stack.setCurrentIndex(index)
        # Hide Save/Clear/Discard/status on the read-only Gesture Reference page
        reference_page = 3
        for w in (self.reload_btn, self.clear_btn, self.save_btn, self.status):
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
        dlg = AppDialog(app_names, parent=self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            app_name = dlg.selected_app()
            if app_name:
                self._add_app_row(app_name)

    def _add_game_row(self, exe_path: str = "", gesture: str = "") -> None:
        """Append a new game row to the game table with a .noui browse button and gesture dropdown."""
        row = self.game_table.rowCount()
        self.game_table.insertRow(row)

        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(2, 2, 2, 2)
        display_name = os.path.basename(exe_path) if exe_path else "No file selected"
        path_label = QtWidgets.QLabel(display_name)
        path_label.setToolTip(exe_path)
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.setFixedWidth(70)
        h_layout.addWidget(path_label, stretch=1)
        h_layout.addWidget(browse_btn)
        self.game_table.setCellWidget(row, 0, container)
        browse_btn.clicked.connect(lambda _, lbl=path_label: self._browse_game_file_into(lbl))

        self._set_gesture_cell(self.game_table, row, gesture, col=1)
        self._refresh_gesture_options()

    def _add_file_row(self, exe_path: str = "", gesture: str = "", uses_camera: bool = False) -> None:
        """Append a new file row to the file table with a browse button, uses-camera checkbox, and gesture dropdown."""
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)

        # Col 0: path label + browse button
        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(2, 2, 2, 2)
        display_name = os.path.basename(exe_path) if exe_path else "No file selected"
        path_label = QtWidgets.QLabel(display_name)
        path_label.setToolTip(exe_path)
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.setFixedWidth(70)
        h_layout.addWidget(path_label, stretch=1)
        h_layout.addWidget(browse_btn)
        self.file_table.setCellWidget(row, 0, container)
        browse_btn.clicked.connect(lambda _, lbl=path_label: self._browse_file_into(lbl))

        # Col 1: uses camera checkbox (centred)
        cb_container = QtWidgets.QWidget()
        cb_layout = QtWidgets.QHBoxLayout(cb_container)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.addStretch()
        cb = QtWidgets.QCheckBox()
        cb.setChecked(uses_camera)
        cb_layout.addWidget(cb)
        cb_layout.addStretch()
        self.file_table.setCellWidget(row, 1, cb_container)

        # Col 2: gesture dropdown
        self._set_gesture_cell(self.file_table, row, gesture, col=2)
        self._refresh_gesture_options()

    def _clear_dynamic_game_rows(self) -> None:
        """Remove all game rows beyond the static No GUI Game Engine row."""
        while self.game_table.rowCount() > 1:
            self.game_table.removeRow(self.game_table.rowCount() - 1)

    def _clear_dynamic_file_rows(self) -> None:
        """Remove all rows from the file table."""
        while self.file_table.rowCount() > 0:
            self.file_table.removeRow(0)

    def _get_cell_path(self, table: QtWidgets.QTableWidget, row: int, col: int = 0) -> str:
        """Return the full path stored in a browse-row cell's path label tooltip."""
        container = table.cellWidget(row, col)
        if container is None:
            return ""
        labels = container.findChildren(QtWidgets.QLabel)
        return labels[0].toolTip() if labels else ""

    def _get_cell_uses_camera(self, table: QtWidgets.QTableWidget, row: int, col: int = 1) -> bool:
        """Return the uses-camera checkbox state from a file-row cell."""
        container = table.cellWidget(row, col)
        if container is None:
            return False
        cbs = container.findChildren(QtWidgets.QCheckBox)
        return cbs[0].isChecked() if cbs else False

    def _browse_game_file_into(self, label: QtWidgets.QLabel) -> None:
        """Open a .noui file dialog and write the selected path into a target label."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Game File", "", "No UI Files (*.noui);;All Files (*)"
        )
        if path:
            full_path = self._to_relative_project_path(os.path.abspath(path))
            label.setText(os.path.basename(path))
            label.setToolTip(full_path)

    def _browse_file_into(self, label: QtWidgets.QLabel) -> None:
        """Open an all-files dialog and write the selected path into a target label."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if path:
            full_path = self._to_relative_project_path(os.path.abspath(path))
            label.setText(os.path.basename(path))
            label.setToolTip(full_path)

    def _all_combos(self):
        """Yield all gesture combos from all tables."""
        for row in range(self.app_table.rowCount()):
            combo = self.app_table.cellWidget(row, 1)
            if combo is not None:
                yield combo
        for row in range(self.game_table.rowCount()):
            combo = self.game_table.cellWidget(row, 1)
            if combo is not None:
                yield combo
        for row in range(self.file_table.rowCount()):
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

        # Game table — static No GUI Game Engine row
        no_gui_action = make_run_action(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)
        no_gui_gesture = action_to_gesture.get(no_gui_action, "")
        self._set_no_gui_game_engine_row(no_gui_gesture)

        # Game table — dynamic game rows
        game_run_paths_list = load_game_run_paths()
        self._clear_dynamic_game_rows()
        for game_path in game_run_paths_list:
            game_action = make_run_action(game_path)
            self._add_game_row(game_path, action_to_gesture.get(game_action, ""))

        # File opening table — all rows are dynamic
        file_entries = load_file_run_entries()
        if not file_entries:
            # backward compat: reconstruct from gesture mapping
            excluded = {no_gui_action} | {make_run_action(p) for p in game_run_paths_list if p}
            old_run = next((a for a in action_to_gesture if is_run_action(a) and a not in excluded), "")
            if old_run:
                file_entries = [{"path": get_run_path(old_run), "uses_camera": load_run_uses_camera()}]
        self._clear_dynamic_file_rows()
        for entry in file_entries:
            file_action = make_run_action(entry["path"])
            self._add_file_row(entry["path"], action_to_gesture.get(file_action, ""), entry["uses_camera"])

        self._camera_view_toggle.blockSignals(True)
        self._camera_view_toggle.setChecked(load_camera_view_enabled())
        self._camera_view_toggle.blockSignals(False)

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

        # Game table — static No GUI Game Engine row
        no_gui_combo = self.game_table.cellWidget(self._GAME_ENGINE_ROW, 1)
        no_gui_gesture = no_gui_combo.currentText().strip() if no_gui_combo else ""
        if no_gui_gesture and no_gui_gesture != "None":
            out[no_gui_gesture] = make_run_action(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)

        # Game table — dynamic game rows (all rows after the engine row)
        for row in range(1, self.game_table.rowCount()):
            path = self._get_cell_path(self.game_table, row)
            combo = self.game_table.cellWidget(row, 1)
            gesture = combo.currentText().strip() if combo else ""
            if path and gesture and gesture != "None":
                out[gesture] = make_run_action(path)

        # File table — all rows are dynamic
        for row in range(self.file_table.rowCount()):
            path = self._get_cell_path(self.file_table, row)
            combo = self.file_table.cellWidget(row, 2)
            gesture = combo.currentText().strip() if combo else ""
            if path and gesture and gesture != "None":
                out[gesture] = make_run_action(path)

        return out

    def clear_selections(self) -> None:
        """
        Reset all gesture selections to blank without saving.
        """
        for combo in self._all_combos():
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

        self._clear_dynamic_game_rows()
        self._clear_dynamic_file_rows()

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

        game_run_paths = [
            self._get_cell_path(self.game_table, row)
            for row in range(1, self.game_table.rowCount())
            if self._get_cell_path(self.game_table, row)
        ]
        file_run_entries = [
            {
                "path": self._get_cell_path(self.file_table, row),
                "uses_camera": self._get_cell_uses_camera(self.file_table, row),
            }
            for row in range(self.file_table.rowCount())
            if self._get_cell_path(self.file_table, row)
        ]
        save_mapping(
            out,
            game_run_paths=game_run_paths,
            file_run_entries=file_run_entries,
            dynamic_apps=dynamic_apps,
            camera_view_enabled=self._camera_view_toggle.isChecked(),
        )
        self.status.setText("Saved to file.")