import pytest
from signals.trade_state_machine import TradeStateMachine, TradeState

# Helper function to trigger a sequence of events
def trigger_events(machine: TradeStateMachine, events: list[str]) -> TradeState:
    for event in events:
        machine.transition_to(event)
    return machine.current_state

def test_initial_state():
    machine = TradeStateMachine()
    assert machine.current_state == TradeState.IDLE

def test_idle_to_scout_transition():
    machine = TradeStateMachine()
    machine.factor_score = 70  # Simulate FactorScore ≥ Θ₁
    machine.transition_to(TradeState.SCOUT)
    assert machine.current_state == TradeState.SCOUT

def test_scout_to_confirm_transition():
    machine = TradeStateMachine()
    machine.transition_to(TradeState.SCOUT)  # Idle -> Scout
    machine.factor_score = 75  # Boundary: FactorScore = Θ₂
    machine.transition_to(TradeState.CONFIRM)
    assert machine.current_state == TradeState.CONFIRM

def test_confirm_to_hold_transition():
    machine = TradeStateMachine()
    machine.transition_to(TradeState.SCOUT)  # Idle -> Scout
    machine.transition_to(TradeState.CONFIRM)  # Scout -> Confirm
    machine.factor_score = 80  # Boundary: FactorScore = Θ₃
    machine.transition_to(TradeState.HOLD)
    assert machine.current_state == TradeState.HOLD

def test_hold_to_exit_tp_transition():
    machine = TradeStateMachine()
    machine.transition_to(TradeState.SCOUT)  # Idle -> Scout
    machine.transition_to(TradeState.CONFIRM)  # Scout -> Confirm
    machine.transition_to(TradeState.HOLD)  # Confirm -> Hold
    machine.transition_to(TradeState.EXIT_TP)  # Hold -> ExitTP
    assert machine.current_state == TradeState.EXIT_TP

def test_exit_tp_to_hold_transition():
    machine = TradeStateMachine()

    # 1) Idle -> Scout
    machine.transition_to(TradeState.SCOUT)

    # 2) Scout -> Confirm
    machine.transition_to(TradeState.CONFIRM)

    # 3) Confirm -> Hold
    machine.transition_to(TradeState.HOLD)

    # 4) Hold -> ExitTP
    machine.transition_to(TradeState.EXIT_TP)
    assert machine.current_state == TradeState.EXIT_TP

    # 5) ExitTP -> Hold (Factor recovery)
    machine.factor_score = 80  # Boundary: FactorScore = Θ₃
    machine.transition_to(TradeState.HOLD)
    assert machine.current_state == TradeState.HOLD

def test_exit_sl_transition():
    machine = TradeStateMachine()
    machine.transition_to(TradeState.SCOUT)  # Idle -> Scout
    machine.transition_to(TradeState.EXIT_SL)  # Scout -> ExitSL
    assert machine.current_state == TradeState.EXIT_SL

def test_end_of_day_transition():
    machine = TradeStateMachine()
    machine.transition_to(TradeState.SCOUT)  # Idle -> Scout
    machine.transition_to(TradeState.CONFIRM)  # Scout -> Confirm
    machine.transition_to(TradeState.HOLD)  # Confirm -> Hold
    machine.transition_to(TradeState.END_OF_DAY)  # Hold -> EndOfDay
    assert machine.current_state == TradeState.END_OF_DAY

def test_invalid_transition():
    machine = TradeStateMachine()
    with pytest.raises(ValueError, match="Invalid transition"):
        machine.transition_to(TradeState.CONFIRM)  # Invalid transition from IDLE

def test_invalid_idle_to_exit_tp_transition():
    machine = TradeStateMachine()
    with pytest.raises(ValueError, match="Invalid transition"):
        machine.transition_to(TradeState.EXIT_TP)  # Invalid transition from Idle

# Add edge case test for factor score boundary
def test_edge_case_factor_score():
    machine = TradeStateMachine()
    machine.transition_to(TradeState.SCOUT)  # Idle -> Scout
    machine.factor_score = 74  # Just below Θ₂
    with pytest.raises(ValueError):
        machine.transition_to(TradeState.CONFIRM)  # Should not transition
    machine.factor_score = 75  # Exactly at Θ₂
    machine.transition_to(TradeState.CONFIRM)  # Should transition
    assert machine.current_state == TradeState.CONFIRM

def test_reset_method():
    machine = TradeStateMachine()
    machine.transition_to(TradeState.SCOUT)  # Idle -> Scout
    machine.transition_to(TradeState.EXIT_SL)  # Scout -> ExitSL
    machine.reset()
    assert machine.current_state == TradeState.IDLE