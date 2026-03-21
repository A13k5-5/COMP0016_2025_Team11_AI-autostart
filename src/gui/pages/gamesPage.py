import os
from collections.abc import Callable

from PySide6 import QtCore, QtWidgets
from src.gui.pages.commonLayouts import (
    build_path_browse_cell,
    create_gesture_combo,
    init_action_gesture_table,
    selected_rows,
    set_readonly_action_cell,
    to_relative_project_path,
)


class GamesPage(QtWidgets.QWidget):
    status_message = QtCore.Signal(str)

    def __init__(
        self,
        supported_gestures: list[str],
        on_gesture_changed: Callable[[], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.supported_gestures = supported_gestures
        self.on_gesture_changed = on_gesture_changed
        self.static_rows = 1

        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(self.static_rows, 2)
        init_action_gesture_table(self.table)

        self.add_btn = QtWidgets.QPushButton("+ Add Game")
        self.delete_btn = QtWidgets.QPushButton("Delete Selected Row")

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self.add_btn)
        button_row.addWidget(self.delete_btn)
        button_row.addStretch()

        layout.addWidget(self.table)
        layout.addLayout(button_row)

        self.add_btn.clicked.connect(lambda: self.add_game_row())
        self.delete_btn.clicked.connect(self._delete_selected_rows)

    def _to_relative_project_path(self, path: str) -> str:
        return to_relative_project_path(__file__, path)

    def _create_gesture_combo(self, current_gesture: str) -> QtWidgets.QComboBox:
        return create_gesture_combo(self.supported_gestures, current_gesture, self.on_gesture_changed)

    def _set_action_cell(self, row: int, action: str) -> None:
        set_readonly_action_cell(self.table, row, action)

    def _set_gesture_cell(self, row: int, gesture: str) -> None:
        combo = self._create_gesture_combo(gesture)
        self.table.setCellWidget(row, 1, combo)

    def set_no_gui_game_engine_row(self, gesture: str = "") -> None:
        self._set_action_cell(0, "No GUI Game Engine")
        self._set_gesture_cell(0, gesture)

    def clear_dynamic_rows(self) -> None:
        while self.table.rowCount() > self.static_rows:
            self.table.removeRow(self.table.rowCount() - 1)

    def add_game_row(self, exe_path: str = "", gesture: str = "", refresh_options: bool = True) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        build_path_browse_cell(self.table, row, exe_path, self._browse_game_file_into)

        self._set_gesture_cell(row, gesture)
        if refresh_options:
            self.on_gesture_changed()

    def _browse_game_file_into(self, label: QtWidgets.QLabel) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Game File",
            "",
            "No UI Files (*.noui);;All Files (*)",
        )
        if path:
            full_path = self._to_relative_project_path(os.path.abspath(path))
            label.setText(os.path.basename(path))
            label.setToolTip(full_path)

    def _selected_rows(self) -> list[int]:
        return selected_rows(self.table)

    def _delete_selected_rows(self) -> None:
        selected_rows = self._selected_rows()
        if not selected_rows:
            self.status_message.emit("Select row(s) in Game Actions to delete.")
            return

        dynamic_rows = [row for row in selected_rows if row >= self.static_rows]
        if not dynamic_rows:
            self.status_message.emit("Built-in rows in Game Actions cannot be deleted.")
            return

        for row in dynamic_rows:
            self.table.removeRow(row)

        self.on_gesture_changed()
        self.status_message.emit("Selected row(s) deleted from Game Actions.")
