# nuitka-project: --mode=standalone
# nuitka-project: --windows-console-mode=disable

# for pyside6
# nuitka-project: --enable-plugin=pyside6

# nuitka-project: --include-package-data=AppOpener

# for gesture reference icons
# nuitka-project: --include-data-dir={MAIN_DIRECTORY}/src/gui/icons=src/gui/icons


# --------------- FOR OPENVINO ----------------
# nuitka-project: --include-package=openvino
# nuitka-project: --include-package-data=openvino
# Include all person detector IR files (xml/bin) in the same runtime path expected by PersonRecogniser
# nuitka-project: --include-data-dir={MAIN_DIRECTORY}/src/video_recogniser/person_recogniser/intel=src/video_recogniser/person_recogniser/intel

# recognizer file for mediapipe
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/video_recogniser/gesture_recogniser/gesture_recognizer.task=src/video_recogniser/gesture_recogniser/gesture_recognizer.task

# settings files
# nuitka-project: --include-data-files=src/gesture_mapping.json=src/gesture_mapping.json
# nuitka-project: --include-data-files=src/app_data.json=src/app_data.json

# icon
# nuitka-project: --include-data-files=icon.png=icon.png
# nuitka-project: --windows-icon-from-ico=icon.png

# nuitka-project: --product-name=AI-Autostart
# nuitka-project: --product-version=1.0.0

from src.system_tray_app import SystemTrayApp

if __name__ == "__main__":
    app = SystemTrayApp()
    app.run()
