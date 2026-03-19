from PySide6 import QtWidgets

from gui.actions import (
    SUPPORTED_GESTURES,
    SUPPORTED_ACTIONS,
    load_mapping,
    load_run_uses_camera,
    load_game_run_paths,
    load_file_run_entries,
    load_dynamic_apps,
    load_camera_view_enabled,
    load_person_recognition_enabled,
    save_camera_view_enabled,
    save_person_recognition_enabled,
    save_mapping,
    make_run_action,
)
from gui.mappingState import build_action_to_gesture, ensure_file_entries, merged_dynamic_apps
from gui.pages.appsPage import AppsPage
from gui.pages.filesPage import FilesPage
from gui.pages.gamesPage import GamesPage
from gui.pages.referencePage import ReferencePage
from gui.tableUtils import (
    collect_dynamic_apps,
    collect_file_run_entries,
    collect_game_run_paths,
    collect_mapping_from_tables,
    iter_gesture_combos,
    refresh_gesture_options,
)


class MappingWindow(QtWidgets.QWidget):
    """Window for configuring gesture-to-action mappings."""

    _GAME_ENGINE_ROW: int = 0
    _NO_GUI_GAME_ENGINE_RELATIVE_PATH = "gameEngine/main.dist/main.exe"
    _ACTION_DISPLAY_NAMES = {
        "stop": "Stop Gesture Recognizer",
    }

    def __init__(self):
        super().__init__()
        self._setup_window("AI-Autostart settings", 620, 520)
        self._create_widgets()
        self._add_widgets()
        self._connect_signals()
        self.load_into_table()

    def _setup_window(self, title: str, width: int, height: int) -> None:
        self.setWindowTitle(title)
        self.resize(width, height)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(4)

    def _create_widgets(self) -> None:
        self._nav_buttons: list[QtWidgets.QPushButton] = []
        for label in ("App Actions", "Game Actions", "File Opening", "Gesture Reference"):
            btn = QtWidgets.QPushButton(label)
            btn.setFlat(True)
            self._nav_buttons.append(btn)

        self.apps_page = AppsPage(
            supported_actions=SUPPORTED_ACTIONS,
            supported_gestures=SUPPORTED_GESTURES,
            action_display_names=self._ACTION_DISPLAY_NAMES,
            on_gesture_changed=self._refresh_gesture_options,
        )
        self.games_page = GamesPage(
            supported_gestures=SUPPORTED_GESTURES,
            on_gesture_changed=self._refresh_gesture_options,
        )
        self.files_page = FilesPage(
            supported_gestures=SUPPORTED_GESTURES,
            on_gesture_changed=self._refresh_gesture_options,
        )
        self.reference_page = ReferencePage()

        self._stack = QtWidgets.QStackedWidget()
        self._stack.addWidget(self.apps_page)
        self._stack.addWidget(self.games_page)
        self._stack.addWidget(self.files_page)
        self._stack.addWidget(self.reference_page)

        self.reload_btn = QtWidgets.QPushButton("Discard Changes")
        self.clear_btn = QtWidgets.QPushButton("Clear Selections")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.status = QtWidgets.QLabel("")
        self.button_row = QtWidgets.QHBoxLayout()

    def _add_widgets(self) -> None:
        nav_bar = QtWidgets.QHBoxLayout()
        nav_bar.setSpacing(0)
        for btn in self._nav_buttons:
            nav_bar.addWidget(btn)
        nav_bar.addStretch()
        self.layout.addLayout(nav_bar)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.layout.addWidget(line)

        self.layout.addWidget(self._stack, stretch=1)

        self.button_row.addWidget(self.reload_btn)
        self.button_row.addWidget(self.clear_btn)
        self.button_row.addWidget(self.save_btn)
        self.layout.addLayout(self.button_row)
        self.layout.addWidget(self.status)

    def _connect_signals(self) -> None:
        self.reload_btn.clicked.connect(self.load_into_table)
        self.clear_btn.clicked.connect(self.clear_selections)
        self.save_btn.clicked.connect(self.save_from_table)

        self.reference_page.camera_view_toggle.toggled.connect(self._save_camera_view_setting)
        self.reference_page.person_recognition_toggle.toggled.connect(self._save_person_recognition_setting)

        self.apps_page.status_message.connect(self.status.setText)
        self.games_page.status_message.connect(self.status.setText)
        self.files_page.status_message.connect(self.status.setText)

        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
        self._navigate(0)

    def _save_camera_view_setting(self, enabled: bool) -> None:
        try:
            save_camera_view_enabled(enabled)
        except Exception as exc:
            self.status.setText(f"Failed to save camera view setting: {exc}")

    def _save_person_recognition_setting(self, enabled: bool) -> None:
        try:
            save_person_recognition_enabled(enabled)
        except Exception as exc:
            self.status.setText(f"Failed to save person recognition setting: {exc}")

    def _navigate(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        reference_page = 3
        for widget in (self.reload_btn, self.clear_btn, self.save_btn, self.status):
            widget.setVisible(index != reference_page)
        for i, btn in enumerate(self._nav_buttons):
            font = btn.font()
            font.setBold(i == index)
            btn.setFont(font)
            btn.setFlat(i != index)

    def load_into_table(self) -> None:
        mapping = load_mapping()
        action_to_gesture = build_action_to_gesture(mapping)

        self.apps_page.populate_static_rows(action_to_gesture)
        self.apps_page.clear_dynamic_rows()
        dynamic_app_names = merged_dynamic_apps(load_dynamic_apps(), action_to_gesture)
        for app_name in dynamic_app_names:
            self.apps_page.add_app_row(
                app_name,
                open_gesture=action_to_gesture.get(f"open:{app_name}", ""),
                close_gesture=action_to_gesture.get(f"close:{app_name}", ""),
                refresh_options=False,
            )

        no_gui_action = make_run_action(self._NO_GUI_GAME_ENGINE_RELATIVE_PATH)
        self.games_page.set_no_gui_game_engine_row(action_to_gesture.get(no_gui_action, ""))

        game_run_paths_list = load_game_run_paths()
        self.games_page.clear_dynamic_rows()
        for game_path in game_run_paths_list:
            game_action = make_run_action(game_path)
            self.games_page.add_game_row(
                game_path,
                action_to_gesture.get(game_action, ""),
                refresh_options=False,
            )

        file_entries = ensure_file_entries(
            file_entries=load_file_run_entries(),
            action_to_gesture=action_to_gesture,
            no_gui_action=no_gui_action,
            game_run_paths=game_run_paths_list,
            fallback_run_uses_camera=load_run_uses_camera(),
            make_run_action=make_run_action,
        )
        self.files_page.clear_rows()
        for entry in file_entries:
            file_action = make_run_action(entry["path"])
            self.files_page.add_file_row(
                entry["path"],
                action_to_gesture.get(file_action, ""),
                entry["uses_camera"],
                refresh_options=False,
            )

        self.reference_page.camera_view_toggle.blockSignals(True)
        self.reference_page.camera_view_toggle.setChecked(load_camera_view_enabled())
        self.reference_page.camera_view_toggle.blockSignals(False)

        self.reference_page.person_recognition_toggle.blockSignals(True)
        self.reference_page.person_recognition_toggle.setChecked(load_person_recognition_enabled())
        self.reference_page.person_recognition_toggle.blockSignals(False)

        self._refresh_gesture_options()
        self.status.setText("Previous selections loaded from file.")

    def _refresh_gesture_options(self) -> None:
        refresh_gesture_options(
            app_table=self.apps_page.table,
            game_table=self.games_page.table,
            file_table=self.files_page.table,
            supported_gestures=SUPPORTED_GESTURES,
        )

    def _collect_mapping_from_table(self) -> dict:
        return collect_mapping_from_tables(
            app_table=self.apps_page.table,
            game_table=self.games_page.table,
            file_table=self.files_page.table,
            supported_gestures=SUPPORTED_GESTURES,
            game_engine_row=self._GAME_ENGINE_ROW,
            no_gui_game_engine_relative_path=self._NO_GUI_GAME_ENGINE_RELATIVE_PATH,
            make_run_action=make_run_action,
        )

    def clear_selections(self) -> None:
        for combo in iter_gesture_combos(self.apps_page.table, self.games_page.table, self.files_page.table):
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

        self.games_page.clear_dynamic_rows()
        self.files_page.clear_rows()

        self._refresh_gesture_options()
        self.status.setText("Selections cleared.")

    def save_from_table(self) -> None:
        out = self._collect_mapping_from_table()
        dynamic_apps = collect_dynamic_apps(self.apps_page.table, self.apps_page.static_rows)
        game_run_paths = collect_game_run_paths(self.games_page.table, start_row=1)
        file_run_entries = collect_file_run_entries(self.files_page.table)
        save_mapping(
            out,
            game_run_paths=game_run_paths,
            file_run_entries=file_run_entries,
            dynamic_apps=dynamic_apps,
            camera_view_enabled=self.reference_page.camera_view_toggle.isChecked(),
            person_recognition_enabled=self.reference_page.person_recognition_toggle.isChecked(),
        )
        self.status.setText("Saved to file.")
