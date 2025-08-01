from enum import Enum, auto
from typing import Literal, Set

class TradeState(Enum):
    """
    Enum representing all possible states of the TradeStateMachine.
    """
    init = auto()
    wait_entry = auto()
    entering = auto()
    entered = auto()
    wait_exit = auto()
    exiting = auto()
    exited = auto()
    failed = auto()

class TradeStateMachine:
    """
    TradeStateMachine implements a strict trading state machine as defined in docs/DESIGN.md.

    States:
        - init: Initial state before any trading action.
        - wait_entry: Waiting for entry signal.
        - entering: Entry order submitted, waiting for fill.
        - entered: Entry order filled, position open.
        - wait_exit: Waiting for exit signal.
        - exiting: Exit order submitted, waiting for fill.
        - exited: Exit order filled, position closed.
        - failed: Terminal error state.

    Only valid transitions are allowed. Invalid events raise an exception.
    All state and event names are lower_snake_case (PEP 8).
    """

    # Allowed transitions: (from_state, event) -> to_state
    _transitions: dict[tuple[TradeState, str], TradeState] = {
        (TradeState.init, "start"): TradeState.wait_entry,
        (TradeState.wait_entry, "entry_signal"): TradeState.entering,
        (TradeState.entering, "entry_filled"): TradeState.entered,
        (TradeState.entering, "entry_failed"): TradeState.failed,
        (TradeState.entered, "exit_signal"): TradeState.exiting,
        (TradeState.exiting, "exit_filled"): TradeState.exited,
        (TradeState.exiting, "exit_failed"): TradeState.failed,
        (TradeState.exited, "reset"): TradeState.wait_entry,
    }
    # Any state can transition to failed on error
    _error_event: str = "error"

    def __init__(self) -> None:
        """
        Initialize the TradeStateMachine in the 'init' state.
        """
        self._state: TradeState = TradeState.init

    @property
    def state(self) -> TradeState:
        """
        Return the current state of the state machine.
        """
        return self._state

    def trigger(self, event: str) -> None:
        """
        Trigger a state transition by event name.

        Args:
            event (str): The event to trigger.

        Raises:
            ValueError: If the event is not a valid transition from the current state.
        """
        # Any state can transition to failed on error
        if event == self._error_event:
            self._state = TradeState.failed
            return

        key = (self._state, event)
        if key in self._transitions:
            self._state = self._transitions[key]
        else:
            raise ValueError(f"Invalid event '{event}' from state '{self._state.name}'.")

    def reset(self) -> None:
        """
        Reset the state machine to the initial state ('init').
        """
        self._state = TradeState.init

    @classmethod
    def valid_states(cls) -> Set[TradeState]:
        """
        Return the set of all valid states.
        """
        return set(TradeState)

    @classmethod
    def valid_events(cls) -> Set[str]:
        """
        Return the set of all valid events.
        """
        events = {"start", "entry_signal", "entry_filled", "entry_failed", "exit_signal", "exit_filled", "exit_failed", "reset", "error"}
        return events 