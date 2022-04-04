from enum import Enum, IntEnum
from typing import Tuple, List, Dict
from random import shuffle
from dataclasses import dataclass


# There are two players:
#   North - on top, moves first
#   South - on bottom, moves second
class Player(IntEnum):
    N = 0
    S = 1

# There are 4 wizards:
#   NorthWest and NorthEast belong to the North player
#   SouthWest and SouthEast belong to the South player
#
# Wizards move around the board, acquire mana, and cast spells to try to kill
# each other.
class Wizard(Enum):
    NW = 0
    NE = 1
    SW = 2
    SE = 3

# Board setup looks like this:
#
#     North Player's Side
#          columns
#         0 1 2 3 4
#        +---------+
#      0 | |W| |W| |
#      1 | | | | | |
# rows 2 |M|S| |M|S|
#      3 | | | | | |
#      4 | |W| |W| |
#        +---------+
#    South Player's Side
#
# Where W is a Wizard, M is a Mana Pool, and S is a Spellbook.
#

# There are two spellbooks with 2 face-down spells each.
# When a wizard moves onto a spellbook, they can examine and swap spells.
class Spellbook(Enum):
    W = 0
    E = 1

# manapools give +1 when a wizard moves onto them
# they are fixed on the board
MANAPOOL_POSITIONS = [(2, 0), (2, 3)]

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
HIDDEN_SPELL = '🀫'


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
    It includes secret information that should not be revealed to the players.
    '''

    # Wizard -> List of spells they have
    # these are only visible to the wizard's player
    #
    # The number of spells per wizard is equivalent to the number of lives; they start at
    # 2 and whenever they lose a life, that spell is removed from this list and added to
    # `dead_spells`.
    #
    # When the list is empty, the wizard is dead.  When both of a player's wizards are dead,
    # they lose.
    wizard_spells: Dict[Wizard, List[Spell]]

    # Spellbook -> the list of spells on that square.
    # There are always exactly two spells in the list.
    spellbook_spells: Dict[Spellbook, List[Spell]]

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

    # the turn counter also tracks the current player (turn_count % 2)
    turn_count: int


def new_state() -> State:
    '''
    Return a new state with the spells randomly dealt.
    '''
    spells = [spell for spell in Spell for s in range(3)]

    # check that we didn't change the count of stuff in the rules and forget to change this method
    assert len(spells) == 15
    assert len(Wizard) == 4
    assert len(Spellbook) == 2

    # shuffle, then deal out the cards from fixed indices
    shuffle(spells)
    return State(
        wizard_spells = {
            Wizard.NW: spells[0:2],
            Wizard.NE: spells[2:4],
            Wizard.SW: spells[4:6],
            Wizard.SE: spells[6:8]
        },
        spellbook_spells = {
            Spellbook.W: spells[8:10],
            Spellbook.E: spells[10:12]
        },
        hidden_spells = spells[12:15],
        wizard_positions = {
            Wizard.NW: (0, 1),
            Wizard.NE: (0, 3),
            Wizard.SW: (4, 1),
            Wizard.SE: (4, 3)
        },
        dead_spells = {wizard: [] for wizard in Wizard},
        turn_count = 0
    )

def check_consistency(state: State) -> None:
    '''
    Check that the spells, wizard lives, and positions are consistent.
    '''

    # check there are exactly 3 of each spell
    spell_counts = {spell: 0 for spell in Spell}
    for spell_list in state.wizard_spells.values():
        assert 0 <= len(spell_list) <= 2
        for spell in spell_list:
            spell_counts[spell] += 1

    for spell_list in state.dead_spells.values():
        assert 0 <= len(spell_list) <= 2
        for spell in spell_list:
            spell_counts[spell] += 1

    for spell_list in state.spellbook_spells.values():
        assert len(spell_list) == 2
        for spell in spell_list:
            spell_counts[spell] += 1

    assert len(state.hidden_spells) == 3
    for spell in state.hidden_spells:
        spell_counts[spell] += 1

    for spell in Spell:
        assert spell_counts[spell] == 3, spell_counts

    for wizard in Wizard:
        # each wizard should have 2 alive or dead spells
        assert len(state.wizard_spells[wizard]) + len(state.dead_spells[wizard]) == 2

        # wizards have a position if and only if they are alive
        assert (len(state.wizard_spells[wizard]) > 0) == (wizard in state.wizard_positions)

    # check no wizards on the same square
    assert len(state.wizard_positions.values()) == len(set(state.wizard_positions.values()))


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


