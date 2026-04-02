from enum import Enum

class GameState(Enum):
    NORMAL = 1
    DECAY = 2
    NIGHTMARE = 3

class StateManager:
    def __init__(self):
        self.state = GameState.NORMAL
        self.day = 1
        self.paranoia_float = 0.0

    def get_state(self):
        return self.state

    def set_state(self, state: GameState):
        self.state = state
