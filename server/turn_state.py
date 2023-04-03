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

    # a special state marking the turn as complete
    # so the game handler can read the turn state, update the game state, and
    # begin the next turn
    TURN_OVER = "TURN_OVER"


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


def _decide_next_choice(turn_state: TurnState, game_state: GameState) -> Tuple[NextChoice, Player]:
    """
    Assumes the previous choice was just decided, and the relevant turn_state field set.

    Returns the next choice and the player making that choice.

    Entering CHOOSE_START and CHOOSE_ACTION are special cases not covered here (see below)
    because they can be accessed by undoing a previous selection.

    But the other choices can only be accessed unambigiously from previous ones
    depending on the previous choices, game state and game logic.

    TODO: synchronize?
    """
    prev = turn_state.next_choice

    # these cases are organized by the outgoing NextChoice - for each state we could
    # enter, we enumerate all the paths by which we can get into that state.

    # opponent may challenge tile-based actions
    if prev == NextChoice.CHOOSE_TARGET and turn_state.action in Tile:
        return NextChoice.RESPOND, game_state.other_player

    # current player may challenge the block
    if prev == NextChoice.RESPOND and self.response == Response.BLOCK:
        return NextChoice.RESPOND_TO_BLOCK, game_state.current_player

    # if the current player successfully used a killing action,
    # opponent replaces the killed tile
    #
    # OH NO
    # grenades can kill multiple opponents and has friendly fire.
    # SIGH
    # TODO: stuck here

    TODO:
        return NextChoice.REPLACE_KILLED, game_state.other_player


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
    # TODO update this
    next_chooser = Player.S

    # record any choices made so far in this turn
    # that are inputs for future choices this turn
    #
    # (start, action, target) will be chosen each turn
    # but we allow changing the selected start & action until the target is chosen
    start: Optional[Square] = None
    action: Optional[Action] = None
    target: Optional[Square] = None

    # the remaining choices are only applicable in certain situations
    response: Optional[Response] = None
    response_to_block: Optional[Response] = None
    replacement_for_kill: Optional[int] = None # index into game_state.tiles_in_hand[player]
    challenge_loss: Optional[Square] = None
    replacement_for_challenge: Optional[int] = None # index into game_state.tiles_in_hand[player]

    def begin_choose_start(self, game_state: GameState):
        """
        Choose the starting tile.  Turns start with this choice, and we can also reach it
        by canceling a previously selected start or action.
        """
        self.next_choice = NextChoice.CHOOSE_START
        self.next_chooser = game_state.current_player
        self.start = None
        self.action = None
        assert self.target is None
        assert self.response is None
        assert self.response_to_block is None
        assert self.replacement_for_kill is None
        assert self.challenge_loss is None
        assert self.replacement_for_challenge is None

    def begin_choose_action(self, game_state: GameState):
        """
        Choose the action.  This happens after choosing the starting tile, or we can reach
        it by canceling a previously selected action.

        Assumes the start square is set.
        """
        self.next_choice = NextChoice.CHOOSE_ACTION
        self.next_chooser = game_state.current_player
        self.action = None
        assert self.start
        assert self.target is None
        assert self.response is None
        assert self.response_to_block is None
        assert self.replacement_for_kill is None
        assert self.challenge_loss is None
        assert self.replacement_for_challenge is None

    def begin_next_choice(self, game_state: GameState):



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
