# nuitka-project: --mode=standalone
# nuitka-project: --windows-console-mode=disable

# for pyside6
## nuitka-project: --enable-plugin=pyside6
## nuitka-project: --include-qt-plugins=qml

# --------------- FOR OPENVINO ----------------
# nuitka-project: --include-package=openvino
# nuitka-project: --include-package-data=openvino

# recognizer file for mediapipe
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/video_recogniser/gesture_recogniser/gesture_recognizer.task=src/video_recogniser/gesture_recogniser/gesture_recognizer.task

# settings files
# nuitka-project: --include-data-files=src/gesture_mapping.json=src/gesture_mapping.json
# nuitka-project: --include-data-files=src/app_data.json=src/app_data.json

# icon
# nuitka-project: --include-data-files=icon.png=icon.png
# nuitka-project: --windows-icon-from-ico=icon.png

# nuitka-project: --product-name=AI-Autostart

from src.system_tray_app import SystemTrayApp

if __name__ == "__main__":
    app = SystemTrayApp()
    app.run()
