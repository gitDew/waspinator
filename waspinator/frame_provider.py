import logging
import os

logger = logging.getLogger(__name__)

class FrameProvider:
    def __iter__(self):
        return self
    def __next__(self):
        raise NotImplementedError
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class PiCameraFrameProvider(FrameProvider):
    def __init__(self, img_size):
        from picamera2 import Picamera2
        import cv2
        self.cv2 = cv2
        self.img_size = img_size
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_preview_configuration(
            main={'size': img_size, 'format': 'RGB888'}
        ))

        self.camera.set_controls({
            "AfMode": 0,
            "LensPosition": 5.4
        })
        self.camera.start()
    def __next__(self):
        frame = self.camera.capture_array()
        frame = self.cv2.resize(frame, self.img_size)
        return frame
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.camera.stop()

class VideoFrameProvider(FrameProvider):
    def __init__(self, path, img_size):
        import cv2
        self.cv2 = cv2
        self.img_size = img_size
        self.cap = self.cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open video: {path}")

    def __next__(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            raise StopIteration
        frame = self.cv2.resize(frame, self.img_size)
        return frame

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cap.release()

class ImageFrameProvider(FrameProvider):
    def __init__(self, path, img_size):
        import cv2
        self.cv2 = cv2
        self.img_size = img_size
        self.path = path
        self.yielded = False

    def __next__(self):
        if self.yielded:
            raise StopIteration
        frame = self.cv2.imread(self.path)
        if frame is None:
            raise ValueError(f"Failed to open image: {self.path}")
        frame = self.cv2.resize(frame, self.img_size)
        self.yielded = True
        logger.info("Loaded image: %s", self.path)
        return frame

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class CSVFrameProvider(FrameProvider):
    def __init__(self, csv_path, img_size):
        import csv
        import cv2
        self.cv2 = cv2
        self.img_size = img_size
        self.image_paths = []
        self.pos = 0
        with open(csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.image_paths.append(row[0])

    def __next__(self):
        if self.pos >= len(self.image_paths):
            raise StopIteration
        path = self.image_paths[self.pos]
        frame = self.cv2.imread(path)
        if frame is None:
            raise ValueError(f"Failed to open image: {path}")
        frame = self.cv2.resize(frame, self.img_size)
        logger.info(path)
        self.pos += 1
        return frame

def get_frame_provider(source, img_size) -> FrameProvider:
    if source == "camera":
        return PiCameraFrameProvider(img_size=img_size)
    ext = os.path.splitext(source)[1].lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
        return ImageFrameProvider(source, img_size=img_size)
    elif ext in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
        return VideoFrameProvider(source, img_size=img_size)
    elif ext == ".csv":
        return CSVFrameProvider(source, img_size=img_size)
    else:
        raise ValueError(f"Unknown source file extension: {ext}")
