# nuitka-project: --mode=standalone

# for pyside6
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-qt-plugins=qml

# --------------- FOR OPENVINO ----------------
# nuitka-project: --include-package=openvino
# nuitka-project: --include-package-data=openvino

# recognizer file for mediapipe
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/video_recogniser/gesture_recogniser/gesture_recognizer.task=src/video_recogniser/gesture_recogniser/gesture_recognizer.task
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/systemTrayDesktopApp/icon.ico=src/systemTrayDesktopApp/icon.ico
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/systemTrayDesktopApp/icon.png=src/systemTrayDesktopApp/icon.png

from src.systemTrayDesktopApp.systemTrayApp import SystemTrayApp


if __name__ == "__main__":
    app = SystemTrayApp()
    app.main()
