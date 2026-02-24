from PySide6 import QtWidgets

from gui.actions import (
    SUPPORTED_GESTURES,
    SUPPORTED_ACTIONS,
    load_mapping,
    save_mapping,
)

class MappingWindow(QtWidgets.QWidget):
    """
    Window for configuring gesture-to-action mappings.
    """

    def __init__(self):
        super().__init__()
        self._setup_window("Customize the mapping between gestures and actions.", 520, 320)
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
        self.table = QtWidgets.QTableWidget(len(SUPPORTED_ACTIONS), 2)
        self.table.setHorizontalHeaderLabels(["Action", "Gesture"])
        self.table.horizontalHeader().setStretchLastSection(True)

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

    def load_into_table(self) -> None:
        """
        Load mapping file and populate table rows.
        """
        mapping = load_mapping()
        action_to_gesture = {a: g for g, a in mapping.items() if a}

        for row, action in enumerate(SUPPORTED_ACTIONS):
            self._set_action_cell(row, action)
            self._set_gesture_cell(row, action_to_gesture.get(action, ""))

        self._refresh_gesture_options()

        self.status.setText("Previous selections loaded from file.")

    def _set_action_cell(self, row: int, action: str) -> None:
        """
        Set the action text in the left column.
        """
        action_item = QtWidgets.QTableWidgetItem(action)
        action_item.setFlags(action_item.flags() & ~QtWidgets.QTableWidgetItem().flags().ItemIsEditable)
        self.table.setItem(row, 0, action_item)

    def _set_gesture_cell(self, row: int, gesture: str) -> None:
        """
        Set a gesture dropdown for the provided row
        """
        combo = self._create_gesture_combo(gesture)
        combo.currentTextChanged.connect(self._refresh_gesture_options)
        self.table.setCellWidget(row, 1, combo)

    def _refresh_gesture_options(self) -> None:
        """
        Keep each dropdown limited to gestures not already used in other rows.
        """
        combos = [self.table.cellWidget(row, 1) for row in range(len(SUPPORTED_ACTIONS))]
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

        for row, action in enumerate(SUPPORTED_ACTIONS):
            combo = self.table.cellWidget(row, 1)
            gesture = combo.currentText().strip()

            if not gesture:
                continue
            out[gesture] = action

        return out

    def clear_selections(self) -> None:
        """
        Reset all gesture selections to blank without saving.
        """
        for row in range(len(SUPPORTED_ACTIONS)):
            combo = self.table.cellWidget(row, 1)
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

        self._refresh_gesture_options()
        self.status.setText("Selections cleared.")

    def save_from_table(self) -> None:
        """
        Persist current table selections to the JSON mapping file.
        """
        out = self._collect_mapping_from_table()
        save_mapping(out)
        self.status.setText("Saved to file.")