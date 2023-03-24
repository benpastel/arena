from enum import Enum
from typing import Optional, Dict, List

from pydantic import BaseModel

from arena.server.state import (
    Square,
    Action,
)


class NextChoice(str, Enum):
    """
    Selecting an action is a state machine:

    values must match JS
    """

    START = "START"
    ACTION = "ACTION"
    TARGET = "TARGET"
    RESPONSE = "RESPONSE"  # TODO


class ActionChooser(BaseModel):
    next_choice = NextChoice.START
    start: Optional[Square] = None
    action: Optional[Action] = None
    target: Optional[Square] = None

    def beginChooseStart(self):
        self.next_choice = NextChoice.START
        self.start = None
        self.action = None
        self.target = None

    def beginChooseAction(self, start: Square):
        self.next_choice = NextChoice.ACTION
        self.start = start
        self.action = None
        self.target = None

    def beginChooseTarget(self, action: Action):
        self.next_choice = NextChoice.TARGET
        assert self.start is not None
        self.action = action
        self.target = None

    def beginWaitForResponse(self, target: Square):
        self.next_choice = NextChoice.RESPONSE
        assert self.start is not None
        assert self.action is not None
        self.target = target

    def tryChooseStart(self, start: Square, positions: List[Square]) -> bool:
        """
        Called when someone clicks on a tile.

        If it's a valid time and choice for a start, returns true and transitions state.

        When state is in ACTION or TARGET, we interpret this as canceling the previously
        selected start and/or action
        """

        if self.next_choice not in (
            NextChoice.START,
            NextChoice.ACTION,
            NextChoice.TARGET,
        ):
            print(f"Ignored {start=} in {self.next_choice}")
            return False

        if start not in positions:
            print(f"Ignored {start=}; not in {positions}")
            return False

        self.beginChooseAction(start)
        return True

    def tryChooseAction(
        self, action: Action, valid_targets: Dict[Action, List[Square]]
    ) -> bool:
        """
        Called when someone clicks on an action.

        If it's a valid time and choice for an action, returns true and transitions state.

        When state is in TARGET, we interpret this as canceling the previously
        selected action
        """
        if self.next_choice not in (NextChoice.ACTION, NextChoice.TARGET):
            print(f"Ignored {action=} in {self.next_choice}")
            return False

        if action not in valid_targets:
            print(f"Ignored {action=}; not in {valid_targets.keys()}.")
            return False

        self.beginChooseTarget(action)
        return True

    def tryChooseTarget(
        self, target: Square, valid_targets: Dict[Action, List[Square]]
    ) -> bool:
        """
        Called when someone clicks on a tile.

        If it's a valid time and choice for a target, return true and transitions state.
        """
        if self.next_choice != NextChoice.TARGET:
            print(f"Ignored {target=} in {self.next_choice}")
            return False

        assert self.action
        if target not in valid_targets[self.action]:
            print(f"Ignored {target=}; not in {valid_targets[self.action]}.")
            return False

        self.beginWaitForResponse(target)
        return True
