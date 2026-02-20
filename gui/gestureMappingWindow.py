from PySide6 import QtWidgets

from gui.actions import (
    SUPPORTED_GESTURES,
    SUPPORTED_ACTIONS,
    load_mapping,
    save_mapping,
)

class MappingWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._setup_window("Customize the mapping between gestures and actions.", 520, 320)
        self._create_widgets()
        self._add_widgets()
        self._connect_signals()
        self.load_into_table()

    def _setup_window(self, title: str, width: int, height: int) -> None:
        self.setWindowTitle(title)
        self.resize(width, height)
        self.layout = QtWidgets.QVBoxLayout(self)

    def _create_widgets(self) -> None:
        self.table = QtWidgets.QTableWidget(len(SUPPORTED_ACTIONS), 2)
        self.table.setHorizontalHeaderLabels(["Action", "Gesture"])
        self.table.horizontalHeader().setStretchLastSection(True)

        self.reload_btn = QtWidgets.QPushButton("Discard Changes")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.status = QtWidgets.QLabel("")

        self.button_row = QtWidgets.QHBoxLayout()

    def _add_widgets(self) -> None:
        self.layout.addWidget(self.table)

        self.button_row.addWidget(self.reload_btn)
        self.button_row.addWidget(self.save_btn)
        self.layout.addLayout(self.button_row)

        self.layout.addWidget(self.status)

    def _connect_signals(self) -> None:
        self.reload_btn.clicked.connect(self.load_into_table)
        self.save_btn.clicked.connect(self.save_from_table)

    def _create_gesture_combo(self, current_gesture: str) -> QtWidgets.QComboBox:
        combo = QtWidgets.QComboBox()
        combo.addItems(SUPPORTED_GESTURES)
        idx = combo.findText(current_gesture)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        return combo

    def load_into_table(self) -> None:
        mapping = load_mapping()  # gesture -> action
        action_to_gesture = {a: g for g, a in mapping.items() if a}

        for row, action in enumerate(SUPPORTED_ACTIONS):
            self._set_action_cell(row, action)
            self._set_gesture_cell(row, action_to_gesture.get(action, ""))

        self.status.setText("Loaded from file.")

    def _set_action_cell(self, row: int, action: str) -> None:
        action_item = QtWidgets.QTableWidgetItem(action)
        action_item.setFlags(action_item.flags() & ~QtWidgets.QTableWidgetItem().flags().ItemIsEditable)
        self.table.setItem(row, 0, action_item)

    def _set_gesture_cell(self, row: int, gesture: str) -> None:
        combo = self._create_gesture_combo(gesture)
        self.table.setCellWidget(row, 1, combo)

    def _collect_mapping_from_table(self) -> tuple[dict, str]:
        out = {g: "" for g in SUPPORTED_GESTURES}
        used = set()

        for row, action in enumerate(SUPPORTED_ACTIONS):
            combo = self.table.cellWidget(row, 1)
            gesture = combo.currentText().strip()

            if not gesture:
                continue
            if gesture in used:
                return out, f"Duplicate gesture selected. Choose a different option."

            used.add(gesture)
            out[gesture] = action

        return out

    def save_from_table(self) -> None:
        out = self._collect_mapping_from_table()
        save_mapping(out)
        self.status.setText("Saved to file.")