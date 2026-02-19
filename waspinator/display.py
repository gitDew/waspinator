import cv2

class FrameDisplay:
    def __init__(self, window_name="Waspinator", width=800, height=600):
        self.window_name = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, width, height)

    def show_and_check_quit(self, frame, quit_key='q', pause=False, step_key=' '):
        cv2.imshow(self.window_name, frame)
        if pause:
            # Wait until space (or quit) is pressed
            while True:
                key = cv2.waitKey(0) & 0xFF
                if key == ord(step_key):
                    return False  # don't quit, advance to next frame
                if key == ord(quit_key):
                    return True  # quit
        else:
            key = cv2.waitKey(1) & 0xFF
            return key == ord(quit_key)

    def close(self):
        cv2.waitKey(0)
        cv2.destroyAllWindows()

