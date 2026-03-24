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
- `src/controller/controller.py` — action orchestration and gesture handling
- `src/controller/powerManager.py` — power mode management
- `src/gui/gestureMappingWindow.py` — settings UI
- `src/gui/actions.py` — mapping/app-data persistence helpers
- `src/video_recogniser/myGestureRecognizer/` — MediaPipe + OpenCV recognition pipeline

## Requirements

- Windows
- Python 3.12
- Webcam

Install dependencies in a fresh virtual environment:

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

## Settings Workflow

In the settings UI, configure mappings in pages:

- **App Actions** — map gestures to open/close app names
- **Game Actions** — map gestures to game/no-UI launch targets
- **File Opening** — map gestures to arbitrary file targets
- **Gesture Reference** — fixed gesture info + camera view toggle

Then click **Save** to persist changes.

## Data Files

- `gesture_mapping.json` — gesture/action config + metadata
- `app_data.json` — app lookup list for `AppOpener`

On tray startup, AI-Autostart refreshes `app_data.json` automatically.

## Tech Stack

- MediaPipe
- OpenCV
- OpenVINO (person detection)
- PySide6
- AppOpener
