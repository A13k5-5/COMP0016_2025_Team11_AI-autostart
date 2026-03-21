# nuitka-project: --mode=standalone

# for pyside6
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-qt-plugins=qml

# --------------- FOR OPENVINO ----------------
# nuitka-project: --include-package=openvino_genai
# nuitka-project: --include-package-data=openvino_genai

# nuitka-project: --include-package=openvino_tokenizers
# nuitka-project: --include-package-data=openvino_tokenizers

# recognizer file for mediapipe
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/src/systemTrayDesktopApp/icon.ico=src/systemTrayDesktopApp/icon.ico

from src.systemTrayDesktopApp.systemTrayApp import main


if __name__ == "__main__":
    main()
