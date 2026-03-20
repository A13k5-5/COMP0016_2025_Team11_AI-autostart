import os

from PySide6 import QtCore, QtWidgets
from myGestureRecognizer.gestureLabels import to_display_text


def init_action_gesture_table(table: QtWidgets.QTableWidget) -> None:
    """Apply common Action/Gesture table layout settings."""
    table.setHorizontalHeaderLabels(["Action", "Gesture"])
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
    header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
    table.setColumnWidth(0, 280)


def create_gesture_combo(
    supported_gestures: list[str],
    current_gesture: str,
    on_gesture_changed,
) -> QtWidgets.QComboBox:
    """Create a gesture combo with None + supported gestures and callback wiring."""
    combo = QtWidgets.QComboBox()
    combo.addItem("None", "")
    for gesture_id in supported_gestures:
        combo.addItem(to_display_text(gesture_id), gesture_id)

    idx = combo.findData(current_gesture)
    combo.setCurrentIndex(idx if idx >= 0 else 0)
    combo.currentIndexChanged.connect(lambda _: on_gesture_changed())
    return combo


def set_readonly_action_cell(
    table: QtWidgets.QTableWidget,
    row: int,
    action: str,
    display_text: str | None = None,
) -> None:
    """Set read-only action text while preserving the canonical action in UserRole."""
    action_item = QtWidgets.QTableWidgetItem(display_text if display_text is not None else action)
    action_item.setData(QtCore.Qt.UserRole, action)
    action_item.setFlags(action_item.flags() & ~QtWidgets.QTableWidgetItem().flags().ItemIsEditable)
    table.setItem(row, 0, action_item)


def selected_rows(table: QtWidgets.QTableWidget) -> list[int]:
    """Return selected table rows in descending order."""
    selection_model = table.selectionModel()
    if selection_model is None:
        return []

    rows = {index.row() for index in selection_model.selectedRows()}
    if not rows:
        rows = {index.row() for index in selection_model.selectedIndexes()}
    if not rows and table.currentRow() >= 0:
        rows = {table.currentRow()}

    return sorted(rows, reverse=True)


def project_root(current_file: str) -> str:
    """Return project root from a page module __file__."""
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


def to_relative_project_path(current_file: str, path: str) -> str:
    """Return project-relative normalized path."""
    return os.path.relpath(path, project_root(current_file)).replace("\\", "/")


def build_path_browse_cell(
    table: QtWidgets.QTableWidget,
    row: int,
    exe_path: str,
    browse_slot,
) -> None:
    """Create and assign a path label + Browse button cell in column 0."""
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
    table.setCellWidget(row, 0, container)
    browse_btn.clicked.connect(lambda _, lbl=path_label: browse_slot(lbl))
