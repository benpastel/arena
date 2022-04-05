from enum import Enum
from typing import Tuple, List, Dict
from random import shuffle
from dataclasses import dataclass


# There are two players:
#   North - displayed on top
#   South - displayed on bottom
class Player(Enum):
    N = 0
    S = 1


# Wizards move around the board, acquire mana, and cast spells to try to kill
# each other.
class Wizard(Enum):
    NW = 0
    NE = 1
    SW = 2
    SE = 3

# which player controls which wizard
PLAYER_TO_WIZARD = {
    Player.N: [Wizard.NW, Wizard.NE],
    Player.S: [Wizard.SW, Wizard.SE]
}

ROWS = 5
COLUMNS = 5
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
# Where W is a Wizard, S is a Sparkle, and  is a Book.

# There are two books with 2 face-down spells each.
# When a wizard moves onto a book, they can examine and swap spells.
class Book(Enum):
    W = 0
    E = 1

BOOK_POSITIONS = {
    Book.W: (2, 1),
    Book.E: (2, 4)
}

# sparkles give +1 when a wizard moves onto them
# they are fixed on the board
SPARKLE_POSITIONS = [(2, 0), (2, 3)]

class Spell(Enum):
    '''
    The spells and their tile representations.

    See spells.py for descriptions and effects.
    '''
    FLOWER_POWER = '🀥'
    GRAPPLING_HOOK = '🀍'
    BIRD_KNIGHT = '🀐'
    CHROMATIC_GRENADES = '🀛'
    BAMBOO_KNIVES = '🀒'

    # This represents a face-down spell tile, where the value is unknown to a player
    HIDDEN = '🀫'


class GameResult(Enum):
    ONGOING = 0
    NORTH_WINS = 1
    SOUTH_WINS = 2

    # a draw is possible if both players are simultaneously killed by a chromatic grenade
    DRAW = 3


@dataclass
class State:
    '''
    This fully represents a game's state.

    There are 3 versions of the state:
        - a private state known only to the server that includes all the spells
        - a player's view on the state where some of the spells are hidden
    '''

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

    # Book -> the list of spells on that square.
    # There are always exactly two spells in the list.
    book_spells: Dict[Book, List[Spell]]

    # The remaining spell tiles are hidden off-board.
    # After an unsuccessful challenge, the challenged spell is first shuffled into this list,
    # and then the wizard draws a new spell from this list.
    hidden_spells: List[Spell]

    # Wizard -> (row, col) position on the board
    # when a wizard is killed they are removed from this dict
    wizard_positions: Dict[Wizard, Tuple[int, int]]

    # Wizard -> the list of spells that have been revealed when this wizard lost a life.
    # these spells stay face-up and are never reshuffled.
    dead_spells: Dict[Wizard, List[Spell]]

    # human-readable event log of public information
    log: List[str]


def new_state() -> State:
    '''
    Return a new state with the spells randomly dealt.
    '''
    spells = [spell for spell in Spell for s in range(3) if spell != Spell.HIDDEN]

    # check that we didn't change the count of stuff in the rules and forget to change this method
    assert len(spells) == 15
    assert len(Wizard) == 4
    assert len(Book) == 2

    # shuffle, then deal out the cards from fixed indices
    shuffle(spells)
    return State(
        wizard_spells = {
            Wizard.NW: spells[0:2],
            Wizard.NE: spells[2:4],
            Wizard.SW: spells[4:6],
            Wizard.SE: spells[6:8]
        },
        book_spells = {
            Book.W: spells[8:10],
            Book.E: spells[10:12]
        },
        hidden_spells = spells[12:15],
        wizard_positions = {
            Wizard.NW: (0, 1),
            Wizard.NE: (0, 3),
            Wizard.SW: (4, 1),
            Wizard.SE: (4, 3)
        },
        dead_spells = {wizard: [] for wizard in Wizard},
        log = []
    )


def player_view(private_state: State, player: Player) -> State:
    '''
    Return a copy of private_state with all hidden spells replaced by Spell.HIDDEN

    This represents the player's knowledge of the state.
    '''
    wizard_spells = {}
    for wizard, spells in private_state.wizard_spells.items():
        if wizard in PLAYER_TO_WIZARD[player]:
            # we can see our wizards' spells
            wizard_spells[wizard] = spells
        else:
            # opponent's wizards' spells are hidden
            wizard_spells[wizard] = [Spell.HIDDEN for _ in spells]

    return State(
        wizard_spells = wizard_spells,
        # we can't see the book spells
        book_spells = {
            Book.W: [Spell.HIDDEN, Spell.HIDDEN],
            Book.E: [Spell.HIDDEN, Spell.HIDDEN],
        },
        # we can't see the hidden spells
        hidden_spells = [Spell.HIDDEN, Spell.HIDDEN, Spell.HIDDEN],
        # we can see everything else
        wizard_positions = private_state.wizard_positions,
        dead_spells = private_state.dead_spells,
        log = private_state.log
    )


def check_consistency(private_state: State) -> None:
    '''
    Check that the spells, wizard lives, and positions are consistent.
    '''

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

    for spell_list in private_state.book_spells.values():
        assert len(spell_list) == 2
        for spell in spell_list:
            spell_counts[spell] += 1

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
        assert len(private_state.wizard_spells[wizard]) + len(private_state.dead_spells[wizard]) == 2

        # wizards have a position if and only if they are alive
        assert (len(private_state.wizard_spells[wizard]) > 0) == (wizard in private_state.wizard_positions)

    # check no wizards on the same square
    assert len(private_state.wizard_positions.values()) == len(set(private_state.wizard_positions.values()))


def check_game_result(state: State) -> GameResult:
    '''
    See if anyone has won the game.
    '''
    north_dead = (
        Wizard.NW not in state.wizard_positions and
        Wizard.NE not in state.wizard_positions
    )
    south_dead = (
        Wizard.SW not in state.wizard_positions and
        Wizard.SE not in state.wizard_positions
    )
    if north_dead and south_dead:
        return GameResult.DRAW
    elif south_dead:
        return GameResult.NORTH_WINS
    elif north_dead:
        return GameResult.SOUTH_WINS
    else:
        return GameResult.ONGOING


