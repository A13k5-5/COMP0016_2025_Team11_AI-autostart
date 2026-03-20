import os
from collections.abc import Callable

from PySide6 import QtCore, QtWidgets
from gui.pages.commonLayouts import (
    build_path_browse_cell,
    create_gesture_combo,
    selected_rows,
    to_relative_project_path,
)


class FilesPage(QtWidgets.QWidget):
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
        self.static_rows = 0

        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Action", "Uses Camera", "Gesture"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 100)

        self.add_btn = QtWidgets.QPushButton("+ Add File")
        self.delete_btn = QtWidgets.QPushButton("Delete Selected Row")

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self.add_btn)
        button_row.addWidget(self.delete_btn)
        button_row.addStretch()

        layout.addWidget(self.table)
        layout.addLayout(button_row)

        self.add_btn.clicked.connect(lambda: self.add_file_row())
        self.delete_btn.clicked.connect(self._delete_selected_rows)

    def _to_relative_project_path(self, path: str) -> str:
        return to_relative_project_path(__file__, path)

    def _create_gesture_combo(self, current_gesture: str) -> QtWidgets.QComboBox:
        return create_gesture_combo(self.supported_gestures, current_gesture, self.on_gesture_changed)

    def add_file_row(
        self,
        exe_path: str = "",
        gesture: str = "",
        uses_camera: bool = False,
        refresh_options: bool = True,
    ) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        build_path_browse_cell(self.table, row, exe_path, self._browse_file_into)

        cb_container = QtWidgets.QWidget()
        cb_layout = QtWidgets.QHBoxLayout(cb_container)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.addStretch()
        cb = QtWidgets.QCheckBox()
        cb.setChecked(uses_camera)
        cb_layout.addWidget(cb)
        cb_layout.addStretch()
        self.table.setCellWidget(row, 1, cb_container)

        combo = self._create_gesture_combo(gesture)
        self.table.setCellWidget(row, 2, combo)
        if refresh_options:
            self.on_gesture_changed()

    def _browse_file_into(self, label: QtWidgets.QLabel) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if path:
            full_path = self._to_relative_project_path(os.path.abspath(path))
            label.setText(os.path.basename(path))
            label.setToolTip(full_path)

    def clear_rows(self) -> None:
        while self.table.rowCount() > 0:
            self.table.removeRow(0)

    def _selected_rows(self) -> list[int]:
        return selected_rows(self.table)

    def _delete_selected_rows(self) -> None:
        selected_rows = self._selected_rows()
        if not selected_rows:
            self.status_message.emit("Select row(s) in File Opening to delete.")
            return

        for row in selected_rows:
            self.table.removeRow(row)

        self.on_gesture_changed()
        self.status_message.emit("Selected row(s) deleted from File Opening.")
