from src.controller.controller import GestureController

def run_gesture_recogniser():
    print("Starting Gesture Recogniser...")
    controller: GestureController = GestureController()
    controller.run()

if __name__ == "__main__":
    run_gesture_recogniser()
