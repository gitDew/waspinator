from collections import deque
from waspinator.trap import TrapCommand, TrapState

VELUTINA = "Vespa_velutina"

def decide(current_state: TrapState, summary_history: deque[list[dict]], is_trap_ready: bool) -> tuple[TrapCommand, TrapState]:

    if not is_trap_ready:
        # Trap is not ready yet; we wait
        return (TrapCommand.NO_OP, current_state)

    if current_state == TrapState.READY_TO_TRIGGER:
        every_summary_has_vespa_velutina = all(any(d.get("name") == VELUTINA for d in summary) for summary in summary_history)
        anything_else_detected = any(any(d.get("name") != VELUTINA for d in frame) for frame in summary_history)

        if not anything_else_detected and every_summary_has_vespa_velutina:
            return (TrapCommand.TRIGGER, TrapState.WAITING_FOR_CLEARANCE)
        return (TrapCommand.NO_OP, current_state)
    elif current_state == TrapState.WAITING_FOR_CLEARANCE:
        any_velutina_detected = any(any(d.get("name") == VELUTINA for d in summary) for summary in summary_history)

        if not any_velutina_detected:
            return (TrapCommand.RESET, TrapState.READY_TO_TRIGGER)
        return (TrapCommand.NO_OP, current_state)
