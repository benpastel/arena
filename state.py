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


# Wizards move around the board, acquire mana, and cast spells to try to kill
# each other.
class Wizard(Enum):
    NW = 0
    NE = 1
    SW = 2
    SE = 3

# which player controls which wizard
PLAYER_TO_WIZARD = {Player.N: [Wizard.NW, Wizard.NE], Player.S: [Wizard.SW, Wizard.SE]}
WIZARD_TO_PLAYER = {
    wizard: player for player, wizards in PLAYER_TO_WIZARD.items() for wizard in wizards
}

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
#      0 | |W| |W| |
#      1 | | | | | |
# rows 2 |S|B| |S|B|
#      3 | | | | | |
#      4 | |W| |W| |
#        +---------+
#    South Player's Side
#
# Where W is a Wizard, S is a Sparkle, and is a Book.

# There are 2 books with 2 face-down spells each.
# When a wizard moves onto a book, they can examine and swap spells.
class Book(Enum):
    W = 0
    E = 1


BOOK_POSITIONS = {Book.W: Square(2, 1), Book.E: Square(2, 4)}

# sparkles give +1 when a wizard moves onto them
# they are fixed on the board
SPARKLE_POSITIONS = [Square(2, 0), Square(2, 3)]


class Spell(Enum):
    """
    The spells and their tile representations.

    See actions.py for descriptions and effects.
    """

    FLOWER_POWER = "🀥"
    GRAPPLING_HOOK = "🀍"
    BIRD_KNIGHT = "🀐"
    CHROMATIC_GRENADES = "🀛"
    BAMBOO_KNIVES = "🀒"

    # This represents a face-down spell tile, where the value is unknown to a player
    HIDDEN = "🀫"



class Action(IntEnum):
    """
    Each turn, each Wizard takes one of these actions.

    Most spells allow a single action, but Bamboo Knives allows 3,
    so we list them all out separately here.

    TODO: spells will also have "double" versions here where you claim two copies of a tile
    which have a more powerful effect.
    """

    # Move 1 square and gain 1 mana
    MOVE = 0

    # Pay 7 mana to kill at any range.
    # If a Wizard has above 10 mana they must smite on their turn.
    SMITE = 1

    # Move 1 and gain 3 mana.
    FLOWER_POWER = 2

    # Pull any enemy to you & steal 2 mana.
    GRAPPLING_HOOK = 3

    # Gain 1 mana & move 1-3 squares.
    BIRD_KNIGHT = 4

    # spend 3 mana to kill @ range 1
    BAMBOO_KNIVES_RANGE_1 = 5

    # spend 5 mana to kill @ range 2
    BAMBOO_KNIVES_RANGE_2 = 6

    # move 2 in any direction, without gaining any mana
    BAMBOO_KNIVES_RUSH = 7

    # target an empty square in a straight line 2 squares away
    # kill in a 3x3 square
    # RULES: change "empty" definition in google doc
    CHROMATIC_GRENADES = 8

# action -> spell enabling that action
# MOVE and SMITE aren't in this dict because they are always enabled
ACTION_TO_SPELL = {
    Action.FLOWER_POWER: Spell.FLOWER_POWER,
    Action.GRAPPLING_HOOK: Spell.GRAPPLING_HOOK,
    Action.BIRD_KNIGHT: Spell.BIRD_KNIGHT,
    Action.BAMBOO_KNIVES_RANGE_1: Spell.BAMBOO_KNIVES,
    Action.BAMBOO_KNIVES_RANGE_2: Spell.BAMBOO_KNIVES,
    Action.BAMBOO_KNIVES_RUSH: Spell.BAMBOO_KNIVES,
    Action.CHROMATIC_GRENADES: Spell.CHROMATIC_GRENADES
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
    BLOCK_WITH_GRAPPLING_HOOK = 2

    # block a grappling hook by claiming to have a bird knight
    BLOCK_WITH_BIRD_KNIGHT = 3


# response -> spell enabling that response
# ACCEPT and CHALLENGE are always enabled
RESPONSE_TO_SPELL = {
    Response.BLOCK_WITH_GRAPPLING_HOOK: Spell.GRAPPLING_HOOK,
    Response.BLOCK_WITH_BIRD_KNIGHT: Spell.BIRD_KNIGHT
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

    # wizard -> list of spells they have
    # each player can only see the spells of their own wizard
    #
    # The number of spells per wizard is equivalent to the number of lives; they start at
    # 2 and whenever they lose a life, that spell is removed from this list and added to
    # `dead_spells`.
    #
    # When the list is empty, the wizard is dead.  When both of a player's wizards are dead,
    # they lose.
    wizard_spells: Dict[Wizard, List[Spell]]

    # Book -> The two spells on that square.
    book_spells: Dict[Book, Tuple[Spell, Spell]]

    # The remaining spell tiles are hidden off-board.
    # After an unsuccessful challenge, the challenged spell is first shuffled into this list,
    # and then the wizard draws a new spell from this list.
    hidden_spells: List[Spell]

    # Wizard -> (row, col) position on the board
    # when a wizard is killed they are removed from this dict
    wizard_positions: Dict[Wizard, Square]

    # Wizard -> the list of spells that have been revealed when this wizard lost a life.
    # these spells stay face-up and are never reshuffled.
    dead_spells: Dict[Wizard, List[Spell]]

    # human-readable event log of public information
    log: List[str]

    # count of turns since beginning of game, starting at 0
    turn_count: int

    def current_wizard(self) -> Wizard:
        '''
        For now the turn order is hardcoded to pass clockwise
        North player starts with 1 turn, then each gets 2 consecutive turns to the end.
        '''
        order = [
            Wizard.NE,
            Wizard.SE,
            Wizard.SW,
            Wizard.NW
        ]
        return order[turn % 4]

    def current_player(self) -> Player:
        return WIZARD_TO_PLAYER[self.current_wizard()]

    def other_player(self) -> Player:
        return other_player(self.current_player())


def new_state() -> State:
    """
    Return a new state with the spells randomly dealt.
    """
    # 3 copies of each spell
    spells = [spell for spell in Spell for s in range(3) if spell != Spell.HIDDEN]

    # check that we didn't change the count of stuff in the rules and forget to change this method
    assert len(spells) == 15
    assert len(Wizard) == 4
    assert len(Book) == 2

    # shuffle, then deal out the cards from fixed indices
    shuffle(spells)
    return State(
        wizard_spells={
            Wizard.NW: spells[0:2],
            Wizard.NE: spells[2:4],
            Wizard.SW: spells[4:6],
            Wizard.SE: spells[6:8],
        },
        book_spells={Book.W: (spells[8], spells[9]), Book.E: (spells[10], spells[11])},
        hidden_spells=spells[12:15],
        wizard_positions={
            Wizard.NW: Square(0, 1),
            Wizard.NE: Square(0, 3),
            Wizard.SW: Square(4, 1),
            Wizard.SE: Square(4, 3),
        },
        dead_spells={wizard: [] for wizard in Wizard},
        log=[],
        turn_count = 0
    )


def player_view(private_state: State, player: Player) -> State:
    """
    Return a copy of private_state with all hidden spells replaced by Spell.HIDDEN

    This represents the player's knowledge of the state.
    """
    wizard_spells = {}
    for wizard, spells in private_state.wizard_spells.items():
        if wizard in PLAYER_TO_WIZARD[player]:
            # we can see our wizards' spells
            wizard_spells[wizard] = spells
        else:
            # opponent's wizards' spells are hidden
            wizard_spells[wizard] = [Spell.HIDDEN for _ in spells]

    return State(
        wizard_spells=wizard_spells,
        # we can't see the book spells
        book_spells={
            Book.W: (Spell.HIDDEN, Spell.HIDDEN),
            Book.E: (Spell.HIDDEN, Spell.HIDDEN),
        },
        # we can't see the hidden spells
        hidden_spells=[Spell.HIDDEN, Spell.HIDDEN, Spell.HIDDEN],
        # we can see everything else
        wizard_positions=private_state.wizard_positions,
        dead_spells=private_state.dead_spells,
        log=private_state.log,
        turn_count = private_state.turn_count
    )


def check_consistency(private_state: State) -> None:
    """
    Check that the spells, wizard lives, and positions are consistent.
    """

    # check there are exactly 3 of each spell
    spell_counts = {spell: 0 for spell in Spell}
    for spell_list in private_state.wizard_spells.values():
        assert 0 <= len(spell_list) <= 2
        for spell in spell_list:
            spell_counts[spell] += 1

    for spell_list in private_state.dead_spells.values():
        assert 0 <= len(spell_list) <= 2
        for spell in spell_list:
            spell_counts[spell] += 1

    for spell_1, spell_2 in private_state.book_spells.values():
        spell_counts[spell_1] += 1
        spell_counts[spell_2] += 1

    assert len(private_state.hidden_spells) == 3
    for spell in private_state.hidden_spells:
        spell_counts[spell] += 1

    for spell in Spell:
        if spell == Spell.HIDDEN:
            assert spell_counts[spell] == 0
        else:
            assert spell_counts[spell] == 3

    for wizard in Wizard:
        # each wizard should have 2 alive or dead spells
        assert (
            len(private_state.wizard_spells[wizard])
            + len(private_state.dead_spells[wizard])
            == 2
        )

        # wizards have a position if and only if they are alive
        assert (len(private_state.wizard_spells[wizard]) > 0) == (
            wizard in private_state.wizard_positions
        )

    # check no wizards on the same square
    assert len(private_state.wizard_positions.values()) == len(
        set(private_state.wizard_positions.values())
    )


def check_game_result(state: State) -> GameResult:
    """
    See if anyone has won the game.
    """
    north_dead = (
        Wizard.NW not in state.wizard_positions
        and Wizard.NE not in state.wizard_positions
    )
    south_dead = (
        Wizard.SW not in state.wizard_positions
        and Wizard.SE not in state.wizard_positions
    )
    if north_dead and south_dead:
        return GameResult.DRAW
    elif south_dead:
        return GameResult.NORTH_WINS
    elif north_dead:
        return GameResult.SOUTH_WINS
    else:
        return GameResult.ONGOING
