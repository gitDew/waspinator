import argparse
from collections import deque
import logging
from ultralytics.models import YOLO
from waspinator.decider import decide
from waspinator.display import FrameDisplay
from waspinator.frame_provider import get_frame_provider
from waspinator.trap import TrapController, FakeTrap, HardwareTrap, TrapState

img_size = (640, 640)
history_length = 3

logger = logging.getLogger(__name__)

def main(model=None, argv=None):
    if model is None:
        model = YOLO('./models/yolo26s-waspinator-chamber.pt', task='detect')

    parser = argparse.ArgumentParser(description='Catch some vespa velutinas.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    start_parser = subparsers.add_parser('start', help='Start the waspinator trap')
    start_parser.add_argument('-s', '--source', default='camera', help='Path to image, video, .csv file or "camera" for webcam. (default:camera)')
    start_parser.add_argument('-d', '--dry-run', action='store_true', help='Enable dry-run mode (trap hardware will not be triggered)')
    start_parser.add_argument('--show', action='store_true', help='Enable frame display')
    start_parser.add_argument('--step', action='store_true', help='Pause after each frame; press space to continue')
    start_parser.add_argument("--log-level", default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"])

    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level)
    if args.command == "start":
        
        trap = FakeTrap() if args.dry_run else HardwareTrap()
        trap_controller = TrapController(trap)
        display = FrameDisplay() if args.show else None

        summary_history = deque([], maxlen=history_length)
        current_state = TrapState.READY_TO_TRIGGER

        with get_frame_provider(args.source, (4608, 2592)) as frame_provider:
            for frame in frame_provider:
                result = model(frame, imgsz=img_size)[0]
                summary_history.append(result.summary())

                command, next_state = decide(current_state, summary_history, trap.ready())

                trap_controller.handle_command(command)
                current_state = next_state

                if display:
                    if display.show_and_check_quit(result.plot(), pause=args.step):
                        break

        if display:
            display.close()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
