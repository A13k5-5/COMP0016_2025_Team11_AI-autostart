import threading

from controller import GestureController

if __name__ == "__main__":
    controller: GestureController = GestureController()
    recogniserThread = threading.Thread(target=controller.run)
    recogniserThread.start()
