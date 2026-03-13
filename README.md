# AI-Autostart

Gesture-controlled desktop automation for Windows.

AI-Autostart uses webcam gesture recognition to trigger actions like opening/closing apps, running files/games, and handling low-power mode gestures.

## What It Does

- Detects supported hand gestures in real time
- Maps gestures to actions via a GUI settings window
- Runs from a system tray menu
- Supports launching files/games with optional camera handoff
- Refreshes installed app list dynamically (`app_data.json`)
- Supports camera preview toggle (default: OFF)

## Project Structure

- `runSystemTray.py` — starts the tray application
- `systemTrayDesktopApp/systemTrayApp.py` — tray icon/menu logic
- `main.py` — starts gesture recognition controller
- `controller.py` — action orchestration and gesture handling
- `gui/gestureMappingWindow.py` — settings UI
- `gui/actions.py` — mapping/app-data persistence helpers
- `myGestureRecognizer/` — MediaPipe + OpenCV recognition pipeline
- `cameraManager.py` — camera handoff for external processes

## Requirements

- Windows
- Python 3.10
- Webcam

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

### 1) Start system tray app

```bash
python runSystemTray.py
```

Tray menu options:

- **Start gesture monitoring**
- **Open settings**
- **Exit**

### 2) Open settings directly (optional)

```bash
python runGUI.py
```

### 3) Run recognizer directly (optional)

```bash
python main.py
```

## Settings Workflow

In the settings UI, configure mappings in pages:

- **App Actions** — map gestures to open/close app names
- **Game Actions** — map gestures to game/no-UI launch targets
- **File Opening** — map gestures to arbitrary file targets
- **Gesture Reference** — fixed gesture info + camera view toggle

Then click **Save** to persist changes.

## Data Files

- `gui/gesture_mapping.json` — gesture/action config + metadata
- `app_data.json` — app lookup list for `AppOpener`

On tray startup, AI-Autostart refreshes `app_data.json` automatically.

## Notes on Run Paths

`run:` actions support both absolute and relative paths.

Relative paths are resolved against the project root at runtime. Missing targets are skipped gracefully with a console warning.


## Tech Stack

- MediaPipe
- OpenCV
- OpenVINO (person detection)
- PySide6
- pystray
- AppOpener
