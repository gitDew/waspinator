import argparse
from collections import deque
import logging
import threading
from ultralytics.models import YOLO
from waspinator.decider import decide
from waspinator.display import FrameDisplay
from waspinator.event_recorder import EventRecorder
from waspinator.frame_provider import get_frame_provider
from waspinator.motion_detector import MotionDetector
from waspinator.trap import TrapController, FakeTrap, HardwareTrap, TrapState
import cv2 as cv

img_size = (640, 384)
history_length = 3

logger = logging.getLogger(__name__)

def main(model=None, argv=None):
    if model is None:
        model = YOLO('./models/yolo26n-waspinator-chamber_ncnn_model', task='detect')

    parser = argparse.ArgumentParser(description='Catch some vespa velutinas.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    start_parser = subparsers.add_parser('start', help='Start the waspinator trap')
    start_parser.add_argument('-s', '--source', default='camera', help='Path to image, video, .csv file or "camera" for webcam. (default:camera)')
    start_parser.add_argument('-d', '--dry-run', action='store_true', help='Enable dry-run mode (trap hardware will not be triggered)')
    start_parser.add_argument('--show', action='store_true', help='Enable frame display')
    start_parser.add_argument('--step', action='store_true', help='Pause after each frame; press space to continue')
    start_parser.add_argument("--log-level", default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"])
    start_parser.add_argument('--record', action='store_true', help='Record motion events to video files')

    setup_parser = subparsers.add_parser('setup', help='Setup the waspinator trap')
    setup_parser.add_argument("--log-level", default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"])

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if args.command == "start":
        trap = FakeTrap() if args.dry_run else HardwareTrap()
        trap_controller = TrapController(trap)
        display = FrameDisplay(pause=args.step) if args.show else None
        motion_detector = MotionDetector()
        event_recorder = EventRecorder("./recordings", img_size) if args.record else None

        with get_frame_provider(args.source, (4608, 2592)) as frame_provider:
            trap_thread = TrapThread(frame_provider, model, trap, trap_controller)
            trap_thread.start()
            while frame_provider.update():
                frame = frame_provider.frame
                assert frame is not None
                frame = cv.resize(frame, img_size)
                if motion_detector.has_motion(frame) and event_recorder is not None:
                    event_recorder.extend_or_start()

                if event_recorder is not None:
                    event_recorder.process_frame(frame)

                if display and trap_thread.annotated_frame is not None:
                    if display.show_and_check_quit(trap_thread.annotated_frame):
                        break

            trap_thread.stop()

        if display:
            display.close()
        if event_recorder:
            event_recorder.stop()
    elif args.command == "setup":
        trap = HardwareTrap()
        trap.setup()
    else:
        parser.print_help()


class TrapThread(threading.Thread):
    def __init__(self, frame_provider, model, trap, trap_controller):
        super().__init__(daemon=True)
        self.running = False
        self.frame_provider = frame_provider
        self.model = model
        self.trap = trap
        self.trap_controller = trap_controller
        self.annotated_frame = None

    def run(self):
        summary_history = deque([], maxlen=history_length)
        current_state = TrapState.READY_TO_TRIGGER

        self.running = True
        while self.running:
            frame = self.frame_provider.frame
            if frame is None:
                continue
            result = self.model(frame, imgsz=img_size[0])[0]
            self.annotated_frame = result.plot()

            summary_history.append(result.summary())

            command, next_state = decide(current_state, summary_history, self.trap.ready())

            self.trap_controller.handle_command(command)

            current_state = next_state

    def stop(self):
        self.running = False

if __name__ == '__main__':
    main()
