import os

from PySide6 import QtCore, QtGui, QtWidgets


_GESTURE_ICONS: list[tuple[str, str, str, str]] = [
    ("Pointing_Up", "icons8-index-pointing-up-48.png", "Pointing Up", "icons8.com/icon/A8CsBXRU88Wm/index-pointing-up"),
    ("Closed_Fist", "icons8-raised-fist-48.png", "Closed Fist", "icons8.com/icon/VkJPr-zo0ySl/raised-fist"),
    ("Victory", "icons8-victory-hand-48.png", "Victory", "icons8.com/icon/T4rG9LrLu-OM/victory-hand"),
    ("ILoveYou", "icons8-love-you-gesture-48.png", "I Love You", "icons8.com/icon/TLeK5N44Q2jW/love-you-gesture"),
    ("Thumb_Up", "icons8-thumbs-up-48.png", "Thumb Up", "icons8.com/icon/FYJ9HNSqf_uK/thumbs-up"),
    ("Thumb_Down", "icons8-thumbs-down-48.png", "Thumb Down", "icons8.com/icon/cPJTvqEzTYvb/thumbs-down"),
    ("Open_Palm", "icons8-raised-hand-48.png", "Open Palm", "icons8.com/icon/ykfYYMYPhA8j/raised-hand"),
]


class ReferencePage(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        display_title = QtWidgets.QLabel("Display Settings")
        font = display_title.font()
        font.setBold(True)
        display_title.setFont(font)
        layout.addWidget(display_title)

        self.camera_view_toggle = QtWidgets.QCheckBox("Show Camera View")
        self.camera_view_toggle.setChecked(False)
        layout.addWidget(self.camera_view_toggle)

        person_row = QtWidgets.QHBoxLayout()
        self.person_recognition_toggle = QtWidgets.QCheckBox("Use Person Recognition")
        self.person_recognition_toggle.setChecked(True)
        person_info_btn = QtWidgets.QToolButton()
        person_info_btn.setText("?")
        person_info_btn.setAutoRaise(True)
        person_info_btn.clicked.connect(self._show_person_recognition_info)
        person_row.addWidget(self.person_recognition_toggle)
        person_row.addWidget(person_info_btn)
        person_row.addStretch()
        layout.addLayout(person_row)

        section_line_1 = QtWidgets.QFrame()
        section_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        section_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(section_line_1)

        fixed_title = QtWidgets.QLabel("Fixed Assignments")
        fixed_title.setFont(font)
        layout.addWidget(fixed_title)

        info_table = QtWidgets.QTableWidget(1, 2)
        info_table.setHorizontalHeaderLabels(["Action", "Gesture"])
        info_header = info_table.horizontalHeader()
        info_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        info_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        info_table.setColumnWidth(0, 280)
        info_table.verticalHeader().hide()
        info_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        info_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        info_table.setFixedHeight(info_table.rowHeight(0) + info_table.horizontalHeader().height() + 4)
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

        layout.addWidget(QtWidgets.QLabel("Available gestures:"))

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        grid_widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(grid_widget)
        grid.setSpacing(16)
        grid.setContentsMargins(8, 8, 8, 8)

        cols = 4
        for idx, (_, icon_file, display_name, attribution) in enumerate(_GESTURE_ICONS):
            cell = QtWidgets.QWidget()
            cell_layout = QtWidgets.QVBoxLayout(cell)
            cell_layout.setAlignment(QtCore.Qt.AlignCenter)
            cell_layout.setSpacing(4)

            icon_label = QtWidgets.QLabel()
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            icon_label.setToolTip(f"Icon by Icons8 — {attribution}")
            icon_path = os.path.join(icons_dir, icon_file)
            pixmap = QtGui.QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                )
            else:
                icon_label.setText("[?]")

            name_label = QtWidgets.QLabel(display_name)
            name_label.setAlignment(QtCore.Qt.AlignCenter)

            cell_layout.addWidget(icon_label)
            cell_layout.addWidget(name_label)
            grid.addWidget(cell, idx // cols, idx % cols)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll, stretch=1)

    def _show_person_recognition_info(self) -> None:
        QtWidgets.QToolTip.showText(
            QtGui.QCursor.pos(),
            "Use Person Recognition narrows gesture analysis to a detected person.\n"
            "If you're alone in a private, low-motion space, disabling it can reduce compute load and improve performance.",
            self,
        )
