from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QColorDialog, QSystemTrayIcon, QMenu
from src.gui.gestureMappingWindow import MappingWindow

app = QApplication([])
app.setQuitOnLastWindowClosed(False)

# Create the icon
icon = QIcon("icon.png")

clipboard = QApplication.clipboard()
mapping_window = MappingWindow()

def copy_color_hex():
    mapping_window.show()

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()
action1 = QAction("Hex")
action1.triggered.connect(copy_color_hex)
menu.addAction(action1)

quit = QAction("Quit")
quit.triggered.connect(app.quit)
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

app.exec()