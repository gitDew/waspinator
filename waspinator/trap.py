from enum import Enum, auto
import logging
import time

logger = logging.getLogger(__name__)

COOLDOWN_SECONDS = 2

class TrapState(Enum):
    WAITING_FOR_CLEARANCE = auto()
    READY_TO_TRIGGER = auto()

class TrapCommand(Enum):
    NO_OP = auto()
    TRIGGER = auto()
    RESET = auto()

class TrapController:
    def __init__(self, trap, initial_state=TrapState.WAITING_FOR_CLEARANCE):
        self.trap = trap
        self.state = initial_state

    def handle_command(self, command: TrapCommand):
        logger.debug("Handling command: %s", command)
        if command == TrapCommand.TRIGGER:
            self.trap.trigger()
        elif command == TrapCommand.RESET:
            self.trap.reset()
        elif command == TrapCommand.NO_OP:
            logger.debug("NO_OP command received; doing nothing.")

        # TODO handle other commands


class FakeTrap:
    """A fake trap implementation for dry-run mode, when we don't want to trigger actual hardware."""
    def trigger(self):
        logger.info("FAKE TRAP TRIGGERED")

    def ready(self) -> bool:
        return True

    def reset(self):
        logger.info("FAKE TRAP RESET")

class HardwareTrap:
    def __init__(self):
        from rpi_hardware_pwm import HardwarePWM

        self.servo = HardwarePWM(pwm_channel=2, chip=0, hz=60)
        self.last_movement = time.time()

    """A trap abstraction that should trigger actual hardware."""
    def trigger(self):
        logger.info("Hardware trap triggered!")
        if not self.ready():
            logger.warning("Trap not ready! Trigger aborted.")
            return
        self.servo.start(12.5)
        time.sleep(1)
        self.servo.stop()
        self.last_movement = time.time()

    def ready(self):
        return (time.time() - self.last_movement > COOLDOWN_SECONDS)

    def reset(self):
        logger.info("Hardware trap resetting!")
        if not self.ready():
            logger.warning("Trap not ready! Reset aborted.")
            return
        self.servo.start(8)
        time.sleep(1)
        self.servo.stop()
        self.last_movement = time.time()
