import cv2 as cv

class MotionDetector:
    def __init__(self):
        self.backSub = cv.createBackgroundSubtractorMOG2(varThreshold=240, detectShadows=True) # high threshold to ignore noise

    def has_motion(self, frame):
        fgMask = self.backSub.apply(frame)
        foreground_only = cv.threshold(fgMask, 200, 255, cv.THRESH_BINARY)[1] # shadows are gray, we want to ignore them
        return self.detect_motion(foreground_only)

    def detect_motion(self, fgMask, min_contour_area=500):
        contours, _ = cv.findContours(fgMask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv.contourArea(contour) > min_contour_area:
                return True
        return False
