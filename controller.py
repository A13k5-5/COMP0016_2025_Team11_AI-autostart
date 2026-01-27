import threading

from myGestureRecognizer import gestureRecogniser

if __name__ == "__main__":
    recogniser = gestureRecogniser.VideoGestureRecogniser()
    recogniserThread = threading.Thread(target=recogniser.run)
    recogniserThread.start()
    while True:
        option = int(input("Choose power mode: \n1. High power mode (30 fps) \n2. Low power mode (1 fps)\n"))
        if option == 1:
            recogniser.set_high_power_mode()
        elif option == 2:
            recogniser.set_low_power_mode()