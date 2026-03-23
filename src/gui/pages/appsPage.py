from collections.abc import Callable

from PySide6 import QtCore, QtWidgets

from src.gui.AppDialog import AppDialog
from src.gui.actions import load_app_data, update_app_data
from src.gui.pages.commonLayouts import (
    create_gesture_combo,
    init_action_gesture_table,
    selected_rows,
    set_readonly_action_cell,
)


class AppsPage(QtWidgets.QWidget):
    status_message = QtCore.Signal(str)

    def __init__(
        self,
        supported_actions: list[str],
        supported_gestures: list[str],
        action_display_names: dict[str, str],
        on_gesture_changed: Callable[[], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.supported_actions = supported_actions
        self.supported_gestures = supported_gestures
        self.action_display_names = action_display_names
        self.on_gesture_changed = on_gesture_changed
        self.static_rows = len(supported_actions)

        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(self.static_rows, 2)
        init_action_gesture_table(self.table)

        self.add_btn = QtWidgets.QPushButton("+ Add App")
        self.update_btn = QtWidgets.QPushButton("Update App List")
        self.delete_btn = QtWidgets.QPushButton("Delete Selected Row")

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self.add_btn)
        button_row.addWidget(self.update_btn)
        button_row.addWidget(self.delete_btn)
        button_row.addStretch()

        layout.addWidget(self.table)
        layout.addLayout(button_row)

        # update app data on init
        update_app_data()
        self.add_btn.clicked.connect(self._open_add_app_dialog)
        self.update_btn.clicked.connect(self._refresh_app_list)
        self.delete_btn.clicked.connect(self._delete_selected_rows)

    def _create_gesture_combo(self, current_gesture: str) -> QtWidgets.QComboBox:
        return create_gesture_combo(self.supported_gestures, current_gesture, self.on_gesture_changed)

    def _set_action_cell(self, row: int, action: str, display_text: str | None = None) -> None:
        set_readonly_action_cell(self.table, row, action, display_text)

    def _set_gesture_cell(self, row: int, gesture: str) -> None:
        combo = self._create_gesture_combo(gesture)
        self.table.setCellWidget(row, 1, combo)

    def populate_static_rows(self, action_to_gesture: dict[str, str]) -> None:
        for row, action in enumerate(self.supported_actions):
            self._set_action_cell(row, action, display_text=self.action_display_names.get(action))
            self._set_gesture_cell(row, action_to_gesture.get(action, ""))

    def clear_dynamic_rows(self) -> None:
        while self.table.rowCount() > self.static_rows:
            self.table.removeRow(self.table.rowCount() - 1)

    def add_app_row(
        self,
        app_name: str,
        open_gesture: str = "",
        close_gesture: str = "",
        refresh_options: bool = True,
    ) -> None:
        for prefix, gesture in (("open", open_gesture), ("close", close_gesture)):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._set_action_cell(row, f"{prefix}:{app_name}")
            self._set_gesture_cell(row, gesture)
        if refresh_options:
            self.on_gesture_changed()

    def _open_add_app_dialog(self) -> None:
        app_names = list(load_app_data().keys())
        dlg = AppDialog(app_names, parent=self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            app_name = dlg.selected_app()
            if app_name:
                self.add_app_row(app_name)

    def _refresh_app_list(self) -> None:
        try:
            update_app_data()
            self.status_message.emit("App list updated.")
        except Exception as exc:
            self.status_message.emit(f"Failed to update app list: {exc}")

    def _selected_rows(self) -> list[int]:
        return selected_rows(self.table)

    def _delete_selected_rows(self) -> None:
        selected_rows = self._selected_rows()
        if not selected_rows:
            self.status_message.emit("Select row(s) in App Actions to delete.")
            return

        dynamic_rows = [row for row in selected_rows if row >= self.static_rows]
        if not dynamic_rows:
            self.status_message.emit("Built-in rows in App Actions cannot be deleted.")
            return

        for row in dynamic_rows:
            self.table.removeRow(row)

        self.on_gesture_changed()
        self.status_message.emit("Selected row(s) deleted from App Actions.")
