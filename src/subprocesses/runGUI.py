import sys
from PySide6.QtWidgets import QApplication
from src.gui.gestureMappingWindow import MappingWindow

def run_gui():
    app = QApplication(sys.argv)
    w = MappingWindow()
    w.show()
    app.exec()

if __name__ == "__main__":
    run_gui()