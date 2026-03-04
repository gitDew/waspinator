from datetime import datetime
import logging
import os
import time
import cv2 as cv
import numpy as np

logger = logging.getLogger(__name__)

class EventRecorder:
    def __init__(self, output_dir: str, img_size: tuple[int, int], fps: float = 30.0):
        self.output_dir = output_dir
        self.fps = fps
        self.writer: cv.VideoWriter | None = None
        self.stop_time: float = 0
        self.current_path: str | None = None
        self.img_size = img_size
        os.makedirs(output_dir, exist_ok=True)
    
    def extend_or_start(self, duration: float = 2.0):
        """Start a new recording or extend current one by duration seconds."""
        self.stop_time = time.time() + duration
        
        if self.writer is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_path = f"{self.output_dir}/motion_{timestamp}.mp4"
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
            self.writer = cv.VideoWriter(self.current_path, fourcc, self.fps, self.img_size)
    
    def write_frame(self, frame: np.ndarray):
        """Write frame if recording is active. Stops if past stop_time."""
        if self.writer is None:
            return
        
        if time.time() < self.stop_time:
            self.writer.write(frame)
        else:
            self.stop()
    
    def stop(self):
        if self.writer:
            self.writer.release()
            logger.info(f"Saved recording: {self.current_path}")
            self.writer = None
            self.current_path = None
