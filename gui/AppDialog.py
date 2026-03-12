from PySide6 import QtWidgets


class AppDialog(QtWidgets.QDialog):
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
