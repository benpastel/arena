from enum import Enum
from typing import Tuple, List, Dict, NamedTuple
from random import shuffle
from dataclasses import dataclass


# There are two players:
#   North - displayed on top
#   South - displayed on bottom
class Player(Enum):
    N = 0
    S = 1


def other_player(p: Player) -> Player:
    return Player.S if p == Player.N else Player.N


ROWS = 5
COLUMNS = 5


class Square(NamedTuple):
    """A coordinate on the board."""

    row: int
    col: int


# Board setup looks like this:
#
#     North Player's Side
#          columns
#         0 1 2 3 4
#        +---------+
#      0 |S| | | |S|
#      1 | | | | | |
# rows 2 |B| |F| |B|
#      3 | | | | | |
#      4 |S| | | |S|
#        +---------+
#    South Player's Side
#
# Where S is a starting spell, F is the mana fountain, B and is a Book.

# There are two spells facedown on each book square.
# when player moves onto a book square & ends their turn on a book square
# they can freely swap that spell
BOOK_POSITIONS = [Square(2, 0), Square(2, 4)]

# The fountain gives +1 mana when someone moves onto it
FOUNTAIN_POSITION = Square(2, 2)

START_POSITIONS = {
    Player.N: (Square(0, 0), Square(0, 4)),
    Player.S: (Square(4, 0), Square(4, 4))
}


class Spell(Enum):
    """
    The spells and their tile representations.

    See actions.py for descriptions and effects.
    """

    FLOWER = "🀥"
    HOOK = "🀍"
    BIRD = "🀐"
    GRENADES = "🀛"
    KNIVES = "🀒"

    # This represents a face-down spell tile, where the value is unknown to a player
    HIDDEN = "🀫"



class Action(IntEnum):
    """
    Each turn, each Wizard takes one of these actions.

    Most spells allow a single action, but Bamboo Knives allows 3,
    so we list them all out separately here.
    """

    # Move 1 square and gain 1 mana
    MOVE = 0

    # Pay 7 mana to kill at any range.
    # If a Wizard has above 10 mana they must smite on their turn.
    SMITE = 1

    # Move 1 and gain 3 mana.
    FLOWER = 2

    # Pull yourself to any enemy & steal 2 mana.
    HOOK = 3

    # Gain 1 mana & move 1-3 squares.
    BIRD = 4

    # spend 3 mana to kill @ range 1
    KNIVES_RANGE_1 = 5

    # spend 5 mana to kill @ range 2
    KNIVES_RANGE_2 = 6

    # target an empty square in a straight line 2 squares away
    # spend 3 mana to kill in a 3x3 square
    GRENADES = 7

# action -> spell enabling that action
# MOVE and SMITE aren't in this dict because they are always enabled
ACTION_TO_SPELL = {
    Action.FLOWER: Spell.FLOWER,
    Action.HOOK: Spell.HOOK,
    Action.BIRD: Spell.BIRD,
    Action.KNIVES_RANGE_1: Spell.KNIVES,
    Action.KNIVES_RANGE_2: Spell.KNIVES,
    Action.GRENADES: Spell.GRENADES
}


class Response(IntEnum):
    '''
    A response by the other player to a proposed action.  Only some responses are valid
    on any given move.

    They choices are to accept, challenge, or block
    but when blocking, the player must choose a blocking spell.

    We flatten the choice of blocking spell into a single enum to simplify
    the player input.

    Only some options are valid on any given move.
    '''

    # accept the action as given
    ACCEPT = 0

    # challenge the action
    CHALLENGE = 1

    # block a grappling hook by claiming to have a grappling hook
    BLOCK_WITH_HOOK = 2

    # block a grappling hook by claiming to have a bird knight
    BLOCK_WITH_BIRD = 3


# response -> spell enabling that response
# ACCEPT and CHALLENGE are always enabled
RESPONSE_TO_SPELL = {
    Response.BLOCK_WITH_HOOK: Spell.HOOK,
    Response.BLOCK_WITH_BIRD: Spell.BIRD
}


class GameResult(Enum):
    ONGOING = 0
    NORTH_WINS = 1
    SOUTH_WINS = 2

    # a draw is possible if both players are simultaneously killed by a chromatic grenade
    DRAW = 3


@dataclass
class State:
    """
    This fully represents a game's state.

    There are 3 versions of the state:
        - a private state known only to the server that includes all the spells
        - each player's view on the state where some of the spells are hidden
    """

    # each player starts with 4 spells in hand.  They then place 2 on the board.
    # when a player runs out of spells they lose.
    spells_in_hand: Dict[Player, List[Spell]]

    # player -> (spell, position of that spell on the board)
    spells_on_board: Dict[Player, List[Tuple[Spell, Square]]]

    # The two spells on each book square.
    book_spells: Dict[Square, Tuple[Spell, Spell]]

    # The remaining spell tiles are hidden off-board and never revealed.
    unused_spells: List[Spell]

    # The list of spells that have been revealed when a player lost a life.
    # These spells stay face-up and are never reshuffled.
    discard: List[Spell]

    # points used to cast spells
    mana: Dict[Player, int]

    # human-readable event log of public information
    log: List[str]

    # count of turns since beginning of game, starting at 0
    turn_count: int

    def current_player(self) -> Player:
        ''' For now, North is hardcoded to go first. '''
        order = [Player.N, Player.S]
        return order[turn % 2]

    def other_player(self) -> Player:
        return other_player(self.current_player())

    def spells_here(self) -> Dict[Square, Spell]:
        ''' Square -> the spell occupying that square '''
        return {
            square: spell
            for spell, square in spells_on_board.values()
        }

    def square_to_player(self) -> Dict[Square, Spell]:
        ''' Square -> the player owning a spell on occupying that square '''
        return {
            square: player
            for player in Player
            for _, square in spells_on_board[player]
        }


def new_state() -> State:
    """
    Return a new state with the spells randomly dealt.
    """
    # 3 copies of each spell
    spells = [spell for spell in Spell for s in range(3) if spell != Spell.HIDDEN]

    # check that we didn't change the count of stuff in the rules and forget to change this method
    assert len(spells) == 15
    assert len(book_spells) == 2

    # shuffle, then deal out the cards from fixed indices
    shuffle(spells)
    return State(
        spells_in_hand={
            Player.N: spells[0:4],
            Player.S: spells[4:8],
        },
        spells_on_board = {},
        book_spells={
            BOOK_POSITIONS[0]: (spells[8], spells[9]),
            BOOK_POSITIONS[1]: (spells[10], spells[11])
        },
        unused_spells=spells[12:15],
        discard=[],
        # first player starts with 1 fewer mana
        mana={Player.N: 1, Player.S: 2},
        log=[],
        turn_count = 0
    )


def player_view(private_state: State, player: Player) -> State:
    """
    Return a copy of private_state with all hidden spells replaced by Spell.HIDDEN

    This represents the player's knowledge of the state.
    """
    opponent = other_player(player)

    # we know the number of spells in the opponent's hand but not their identity
    opponent_hand = [
        Spell.HIDDEN
        for spell in private_state.spells_in_hand[opponent]
    ]
    # we know the number and location of spells on the opponent's board but not their
    # identity
    opponent_board = [
        (Spell.HIDDEN, square)
        for spell, square in private_state.spells_on_board[opponent]
    ]

    return State(
        spells_in_hand={
            player: private_state.spells_in_hand[player],
            opponent: opponent_hand,
        },
        spells_on_board={
            player: private_state.spells_on_board[player],
            opponent: opponent_board
        },
        # we can't see the book spells
        book_spells={
            Book.W: (Spell.HIDDEN, Spell.HIDDEN),
            Book.E: (Spell.HIDDEN, Spell.HIDDEN),
        },
        # we can't see the unused spells
        unused_spells=[Spell.HIDDEN, Spell.HIDDEN, Spell.HIDDEN],
        # we can see everything else
        discard=private_state.discard,
        log=private_state.log,
        turn_count = private_state.turn_count
    )


def check_consistency(private_state: State) -> None:
    """
    Check that the spells are consistent.
    """

    # check there are exactly 3 of each spell
    spell_counts = {spell: 0 for spell in Spell}
    for spell_list in private_state.spells_in_hand.values():
        assert 0 <= len(spell_list) <= 2
        for spell in spell_list:
            spell_counts[spell] += 1

    for spell_list in private_state.spells_on_board.values():
        assert 0 <= len(spell_list) <= 2
        for spell in spell_list:
            spell_counts[spell] += 1

    for spell in private_state.discard:
        spell_counts[spell] += 1

    for spell_1, spell_2 in private_state.book_spells.values():
        spell_counts[spell_1] += 1
        spell_counts[spell_2] += 1

    assert len(private_state.unused_spells) == 3
    for spell in private_state.unused_spells:
        spell_counts[spell] += 1

    for spell in Spell:
        if spell == Spell.HIDDEN:
            assert spell_counts[spell] == 0
        else:
            assert spell_counts[spell] == 3


def check_game_result(state: State) -> GameResult:
    """
    See if anyone has won the game.
    """
    north_dead = (
        len(spells_on_board[Player.N]) + len(spells_in_hand[Player.N]) == 0
    )
    south_dead = (
        len(spells_on_board[Player.S]) + len(spells_in_hand[Player.S]) == 0
    )
    if north_dead and south_dead:
        return GameResult.DRAW
    elif south_dead:
        return GameResult.NORTH_WINS
    elif north_dead:
        return GameResult.SOUTH_WINS
    else:
        return GameResult.ONGOING
