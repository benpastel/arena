from enum import Enum
from typing import Tuple, List

ROWS = 5
COLUMNS = 5

# There are two players:
#   North - on top, moves first
#   South - on bottom, moves second
class Player(Enum):
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
# We represent the board with two objects:
#   - a 5x5 array


class Square(IntEnum):
    EMPTY = 0

    # manapools give +1 when a wizard moves onto them
    MANAPOOL = 1

    # each spellbook has 2 face-down spell tiles
    # wizards can examine and swap spell tiles when they move onto a spellbook
    SPELLBOOK_W = 2
    SPELLBOOK_E = 3

# BOARD is a fixed array representing the position of the manapools and spellbooks
# the wizard positions are tracked separately in a coordinate dict
BOARD = np.full((ROWS, COLUMNS), Square.EMPTY, dtype=int)
BOARD[2, 0] = Square.MANAPOOL
BOARD[2, 1] = Square.SPELLBOOK_W
BOARD[2, 3] = Square.MANAPOOL
BOARD[2, 4] = Square.SPELLBOOK_E


class State:
    #
    wizard_positions: Dict[Wizard, Tuple(int, int)]



def new_state() -> State:
    # Represent the board state as a dict wizard => (row, col) location of that wizard
    #








