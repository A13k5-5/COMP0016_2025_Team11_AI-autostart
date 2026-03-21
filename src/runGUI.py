import sys
from PySide6.QtWidgets import QApplication
from src.gui.gestureMappingWindow import MappingWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MappingWindow()
    w.show()
    app.exec()