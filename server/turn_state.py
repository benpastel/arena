from enum import Enum
from typing import Optional, Dict, List

from pydantic import BaseModel

from arena.server.state import (
    Square,
    Action,
    Player
)

class NextChoice(str, Enum):
    """
    The next choice for either player to make within this turn.
    """

    # choose the start square
    CHOOSE_START = "CHOOSE_START"

    # choose the action for that start square, or change the start square selection
    CHOOSE_ACTION = "CHOOSE_ACTION"

    # choose the target for that action, or change the start square / action selection
    CHOOSE_TARGET = "CHOOSE_TARGET"

    # choose whether to challenge the action
    # applicable for all actions except MOVE or SMITE
    RESPOND = "RESPOND"

    # choose whether to challenge the response
    # applicable if the grapple was blocked
    RESPOND_TO_BLOCK = "RESPOND_TO_BLOCK"

    # choose a tile from hand to replace one killed
    # if the player still has tile(s) in hand
    REPLACE_KILLED = "REPLACE_KILLED"

    # choose a tile on board to lose if the enemy successfully challenged
    # or we unsuccessfully challenged
    CHOOSE_CHALLENGE_LOSS = "CHOOSE_CHALLENGE_LOSS"

    # choose a tile from hand to replace the one lost from a challenge
    # if the player still has tile(s) in hand
    REPLACE_CHALLENGE_LOSS = "REPLACE_CHALLENGE_LOSS"


class Response(str, Enum):
    """
    A response by the other player to a proposed action.  Only some responses are valid
    on any given move.
    """

    # accept the action as given
    ACCEPT = "ACCEPT"

    # challenge the action
    CHALLENGE = "CHALLENGE"

    # block a grappling hook by claiming to have a grappling hook
    # if the rules change to allow other blocks, there should be a separate
    # response type for each claimed tile
    BLOCK = "BLOCK"


class TurnState(BaseModel):
    """
    The within-turn state, consisting of players' choices so far:
        which actions have been chosen
        which challenges / blocks / etc have been chosen
        which tiles have been chosen to be lost
    """

    # the next choice for either player to make during this turn
    next_choice = NextChoice.CHOOSE_START

    # the player responsible for making that choice
    # for now we hardcode south player as starting
    next_chooser = Player.S

    # record any choices made so far in this turn
    # that are inputs for future choices this turn
    #
    # (start, action, target) will always be chosen
    # the rest are only applicable in some situations
    start: Optional[Square] = None
    action: Optional[Action] = None
    target: Optional[Square] = None

    # TODO from here we need to decide:
    #   are we updating game_state as we go?  or relegating to end-of-turn
    #
    # if updating game_state as we go, those updates need to be intermingled with these
    # try_ or begin_ functions
    #
    # if relegating to end-of-turn, we'll need to recompute challenge failure twice
    # also, the two "REPLACE LOSS" functions are confusing if happen simultaneously
    # ... although I guess they can't happen simultaneously because you can only ever
    #   choose once??
    #
    # ok let's go with that idea, and maybe make a special state out of it
    # to tell the handler it's time to compute the end-of-turn
    response: Optional[Response] = None
    response_to_block: Optional[Response] = None
    kill_replacement: Optional[int] = None # index into game_state.tiles_in_hand[player]
    challenge_loss: Optional[Square] = None
    challenge_replacement: Optional[int] = None # index into game_state.tiles_in_hand[player]

    """
    The following state transitions assume that a valid choice has been made.

    They record the previous choice, and transition us to waiting on the next choice.
    They sometimes need the game state as context for determining the next choice.
    """
    def begin_choose_start(self):
        self.next_choice = NextChoice.CHOOSE_START
        self.start = None
        self.action = None
        self.target = None
        self.response = None
        self.response_to_block = None
        self.kill_replacement = None
        self.challenge_loss = None
        self.challenge_replacement = None

    def begin_choose_action(self, start: Square):
        self.next_choice = NextChoice.CHOOSE_ACTION
        self.start = start
        self.action = None
        self.target = None

    def begin_choose_target(self, action: Action):
        assert self.start
        self.next_choice = NextChoice.CHOOSE_TARGET
        self.action = action
        self.target = None

    def begin_respond(self, target: Square):
        assert self.start
        assert self.action
        assert self.target is None
        self.next_choice = NextChoice.RESPOND
        self.target = target

    def begin_respond_to_block(self):
        assert self.start
        assert self.action
        assert self.target
        assert self.response is None
        assert response == response.
        self.target = None
        self.response = None



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
