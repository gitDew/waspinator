from datetime import datetime
import logging
import os
import shutil
import cv2 as cv
import numpy as np

logger = logging.getLogger(__name__)

class EventRecorder:
    def __init__(self, output_dir: str, img_size: tuple[int, int], fps: float = 15.0):
        self.output_dir = output_dir
        self.fps = fps
        self.writer: cv.VideoWriter | None = None
        self.stop_time: float = 0
        self.current_path: str | None = None
        self.img_size = img_size
        os.makedirs(output_dir, exist_ok=True)
        self.frames_recorded = 0
        self.frames_total = 0
        self.max_frames = int(fps * 60 * 5)  # max 5 minutes per recording to prevent huge files
    
    def extend_or_start(self, duration: int = 2):
        """Start a new recording or extend current one by duration seconds."""
        if self.writer is None:
            _, _, free = shutil.disk_usage(self.output_dir)
            min_space_bytes = 1 * 1024**3  # 1GB
            if free < min_space_bytes:
                logger.warning("Insufficient disk space: less than 1GB available. Not allowing new recording.")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_path = f"{self.output_dir}/motion_{timestamp}.mp4"
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
            self.writer = cv.VideoWriter(self.current_path, fourcc, self.fps, self.img_size)
            self.frames_recorded = 0
            self.frames_total = 0

        self.frames_total = self.frames_recorded + (duration * self.fps)

    def process_frame(self, frame: np.ndarray):
        """Write frame if recording is active. Stops if past total frames or max frames."""
        if self.writer is None:
            return
        
        if self.frames_recorded < self.frames_total and self.frames_recorded < self.max_frames:
            self.frames_recorded += 1
            self.writer.write(frame)
        else:
            self.stop()
    
    def stop(self):
        if self.writer:
            self.writer.release()
            logger.info(f"Saved recording: {self.current_path}")
            self.writer = None
            self.current_path = None
            self.frames_recorded = 0
            self.frames_total = 0
