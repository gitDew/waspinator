from collections import deque
from waspinator.patience_countdown import PatienceCountdown
from waspinator.trap import TrapCommand, TrapState

VELUTINA = "Vespa_velutina"

def decide(current_state: TrapState, summary_history: deque[list[dict]], is_trap_ready: bool, patience: PatienceCountdown) -> tuple[TrapCommand, TrapState]:

    if not is_trap_ready:
        # Trap is not ready yet; we wait
        return (TrapCommand.NO_OP, current_state)

    if current_state == TrapState.READY_TO_TRIGGER:
        every_summary_has_vespa_velutina = all(any(d.get("name") == VELUTINA for d in summary) for summary in summary_history)
        anything_else_detected = any(any(d.get("name") != VELUTINA for d in frame) for frame in summary_history) # with the current model this can only be a crabro, other insects would not trigger a detection

        if not anything_else_detected and every_summary_has_vespa_velutina:
            patience.reset()
            return (TrapCommand.TRIGGER, TrapState.WAITING_FOR_CLEARANCE)
        
        # we still haven't detected a velutina: our patience is running thin
        patience.tick()
        if patience.ran_out():
            patience.reset()
            return (TrapCommand.SLEEP, TrapState.READY_TO_TRIGGER) # we're going back to sleep

    elif current_state == TrapState.WAITING_FOR_CLEARANCE:
        latest_summary = summary_history[-1]
        any_velutina_detected = any(d.get("name") == VELUTINA for d in latest_summary)

        if not any_velutina_detected:
            return (TrapCommand.RESET, TrapState.READY_TO_TRIGGER)
        return (TrapCommand.WAIT, current_state) # wait a bit until the next inference

    return (TrapCommand.NO_OP, current_state)
