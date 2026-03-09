import argparse
import logging
import time
from waspinator.decider import decide
from waspinator.display import FrameDisplay
from waspinator.event_recorder import EventRecorder
from waspinator.frame_provider import get_frame_provider
from waspinator.motion_detector import MotionDetector
from waspinator.trap import TrapCommand, TrapController, FakeTrap, HardwareTrap, TrapState
from waspinator.patience_countdown import PatienceCountdown
import cv2 as cv
from multiprocessing import Queue, Process, Event

img_size = (640, 384)

logger = logging.getLogger(__name__)

def main(argv=None):
    model_path = './models/yolo26n-waspinator-chamber_ncnn_model'

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

        frame_queue = Queue(maxsize=1)
        with get_frame_provider(args.source, (4608, 2592)) as frame_provider:
            run_inference_event = Event()
            shutdown_event = Event()
            trap_process = Process(
                target=trap_worker,
                args=(frame_queue, model_path, trap, trap_controller, run_inference_event, shutdown_event)
            )
            trap_process.start()
            while frame_provider.update():
                frame = frame_provider.frame
                assert frame is not None
                frame = cv.resize(frame, img_size)
                if motion_detector.has_motion(frame): 
                    if not run_inference_event.is_set():
                        logger.info("Motion detected; signaling trap process to run inference.")
                        run_inference_event.set()
                    if event_recorder is not None:
                        event_recorder.extend_or_start()

                
                # Add to trap/inference queue
                try:
                    # we use a queue of size 1 to always have the latest frame for inference, dropping older frames if the trap worker is still processing
                    if frame_queue.full():
                        frame_queue.get_nowait()
                except:
                    pass
                frame_queue.put(frame)

                if event_recorder is not None:
                    event_recorder.process_frame(frame)

                if display:
                    if display.show_and_check_quit(frame):
                        break


        if display:
            display.close()
        if event_recorder:
            event_recorder.stop()

        shutdown_event.set() # signal trap_worker to exit
        run_inference_event.set() # resume trap_worker so it can exit
        try:
            if frame_queue.full():
                frame_queue.get_nowait()
        except:
            pass
        frame_queue.put(None)
        trap_process.join() # wait for the trap_worker process to finish

    elif args.command == "setup":
        trap = HardwareTrap()
        trap.setup()
    else:
        parser.print_help()

def trap_worker(frame_queue, model_path, trap, trap_controller: TrapController, run_inference_event, shutdown_event):
    from collections import deque
    from ultralytics.models import YOLO
    history_length = 3
    patience_length = 30
    cooldown_seconds = 60
    confidence_threshold = 0.8
    
    model = YOLO(model_path, task='detect')
    summary_history = deque([], maxlen=history_length)
    current_state = TrapState.READY_TO_TRIGGER
    patience_countdown = PatienceCountdown(patience_length) # After how many cycles of no detection do we pause the inference loop

    while True:
        run_inference_event.wait() # Wait until the main process signals to run inference
        if shutdown_event.is_set():
            logger.info("Shutdown event received; exiting trap worker.")
            return

        frame = frame_queue.get()
        if frame is None:
            return

        result = model(frame, imgsz=img_size[0], conf=confidence_threshold)[0]
        summary_history.append(result.summary())

        command, next_state = decide(current_state, summary_history, trap.ready(), patience_countdown)
        trap_controller.handle_command(command)
        current_state = next_state

        if command == TrapCommand.SLEEP:
            logger.info(f"No velutina detected for {patience_length} cycles. Entering cooldown for {cooldown_seconds} seconds.")
            start = time.time()
            while time.time() - start < cooldown_seconds:
                if shutdown_event.is_set():
                    logger.info("Shutdown event received during cooldown; exiting trap worker.")
                    return
                time.sleep(1)
            logger.info("Trap worker cooldown elapsed. Inference will resume on next motion detection.")
            run_inference_event.clear()

if __name__ == '__main__':
    main()
