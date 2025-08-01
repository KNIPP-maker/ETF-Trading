class StateMachine:
    """A simple state machine base class."""
    def __init__(self, initial_state):
        self.state = initial_state

    def transition(self, new_state):
        """Transition to a new state."""
        self.state = new_state

    def get_state(self):
        """Return the current state."""
        return self.state 