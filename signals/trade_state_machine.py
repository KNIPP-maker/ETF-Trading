from typing import Optional
from enum import Enum

class TradeState(Enum):
    IDLE = "Idle"
    SCOUT = "Scout"
    CONFIRM = "Confirm"
    HOLD = "Hold"
    EXIT_TP = "ExitTP"
    EXIT_SL = "ExitSL"
    END_OF_DAY = "EndOfDay"

class TradeStateMachine:
    """
    A finite-state machine for managing trade states and transitions.

    States:
        - Idle
        - Scout
        - Confirm
        - Hold
        - ExitTP
        - ExitSL
        - EndOfDay

    Transitions and entry actions are defined based on the specification in DESIGN.md.
    """

    def __init__(self):
        self.current_state: TradeState = TradeState.IDLE
        self.factor_score: Optional[float] = None
        self.risk_budget: float = 0.0

    def transition_to(self, new_state: TradeState):
        """
        Handles state transitions and executes entry actions.

        Args:
            new_state (TradeState): The state to transition to.

        Raises:
            ValueError: If the transition is invalid.
        """
        valid_transitions = {
            TradeState.IDLE: [TradeState.SCOUT],
            TradeState.SCOUT: [TradeState.CONFIRM, TradeState.EXIT_SL],
            TradeState.CONFIRM: [TradeState.HOLD, TradeState.EXIT_SL],
            TradeState.HOLD: [TradeState.EXIT_TP, TradeState.EXIT_SL, TradeState.END_OF_DAY],
            TradeState.EXIT_TP: [TradeState.HOLD, TradeState.EXIT_SL, TradeState.END_OF_DAY],
            TradeState.EXIT_SL: [TradeState.IDLE],
            TradeState.END_OF_DAY: [TradeState.IDLE],
        }

        if new_state not in valid_transitions.get(self.current_state, []):
            raise ValueError(f"Invalid transition from {self.current_state} to {new_state}")

        self.current_state = new_state
        self._execute_entry_action(new_state)

    def _execute_entry_action(self, state: TradeState):
        """
        Executes entry actions for the given state.

        Args:
            state (TradeState): The state for which to execute entry actions.
        """
        if state == TradeState.IDLE:
            self._idle_entry_action()
        elif state == TradeState.SCOUT:
            self._scout_entry_action()
        elif state == TradeState.CONFIRM:
            self._confirm_entry_action()
        elif state == TradeState.HOLD:
            self._hold_entry_action()
        elif state == TradeState.EXIT_TP:
            self._exit_tp_entry_action()
        elif state == TradeState.EXIT_SL:
            self._exit_sl_entry_action()
        elif state == TradeState.END_OF_DAY:
            self._end_of_day_entry_action()

    def _idle_entry_action(self):
        """Entry action for the Idle state."""
        print("No orders – begin factor monitoring")

    def _scout_entry_action(self):
        """Entry action for the Scout state."""
        print("Place OCO order: hard stop = entry × 0.997 (-0.3%), soft limit = entry × 1.005")

    def _confirm_entry_action(self):
        """Entry action for the Confirm state."""
        print("Add size; refresh OCO (new avg price, same % stop)")

    def _hold_entry_action(self):
        """Entry action for the Hold state."""
        print("Trail soft stop to VWAP – 1 tick every 20 ticks")

    def _exit_tp_entry_action(self):
        """Entry action for the ExitTP state."""
        print("Adjust risk-budget & refresh trailing stop")

    def _exit_sl_entry_action(self):
        """Entry action for the ExitSL state."""
        print("Log loss, freeze same symbol for 5 min (order cool-down)")

    def _end_of_day_entry_action(self):
        """Entry action for the EndOfDay state."""
        print("Write EOD PnL row, disable new signals until next session")

    def reset(self):
        """
        Resets the state machine to the initial state (IDLE).
        """
        self.current_state = TradeState.IDLE