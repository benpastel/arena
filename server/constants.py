from enum import Enum
from typing import Literal, NamedTuple


# There are two players:
#   North - displayed on top
#   South - displayed on bottom
#
# the enum values must match the javascript & css values
class Player(str, Enum):
    N = "north"
    S = "south"


def other_player(p: Player) -> Player:
    return Player.S if p == Player.N else Player.N


ROWS = 5
COLUMNS = 5


class Square(NamedTuple):
    """A coordinate on the board."""

    row: int
    col: int

    def on_board(self) -> bool:
        """True if the square is in-bounds on the board."""
        return 0 <= self.row < ROWS and 0 <= self.col < COLUMNS

    @classmethod
    def from_list(cls, coords: list) -> "Square":
        assert len(coords) == 2
        row, col = coords
        return cls(row, col)


# Board setup looks like this:
#
#     North Player's Side
#          columns
#         1 2 3 4 5
#        +---------+
#      A |S| | | |S|
#      B | | | | | |
# rows C |B| |F| |B|
#      D | | | | | |
#      E |S| | | |S|
#        +---------+
#    South Player's Side
#
# Where S is a tile in play, F is the mana fountain, B and is a Book.

# There are two tiles facedown on each book square.
# when player moves onto a book square & ends their turn on a book square
# they can freely swap those tiles
# TODO implement these
BOOK_POSITIONS = [Square(2, 0), Square(2, 4)]

# The fountain gives +1 mana when someone moves onto it
FOUNTAIN_POSITION = Square(2, 2)

# TODO randomize instead
START_POSITIONS = {
    Player.N: (Square(0, 0), Square(0, 4)),
    Player.S: (Square(4, 0), Square(4, 4)),
}


class Tile(str, Enum):
    """
    The game pieces.

    Each tile enables one special action.

    You can always do the special action of any tile, but will lose a life
    if challenged and you aren't that tile.
    """

    # move 1 & gain 3 mana
    FLOWER = "🀥"

    # pull yourself to any enemy at a Queen move & steal 2 mana
    HOOK = "🀍"

    # move 1-2 & gain 2 mana
    BIRD = "🀐"

    # spend 3 mana to kill in a 3x3 square
    # around an empty square 2 squares away in a cardinal direction
    GRENADES = "🀛"

    # spend:
    #   - 3 mana to kill @ range 1
    #   - 5 mana to kill @ range 2
    KNIVES = "🀒"

    # Represents a tile with value unknown to a player
    # there is a private state known only to the game engine with no hidden tiles;
    # each player has a view with some of the tiles replaced with HIDDEN
    HIDDEN = "🀫"

    def __str__(self) -> str:
        return f"{self.value} ({self.name.lower()})"


class OtherAction(str, Enum):
    """
    These actions are always allowed for any tile.
    """

    # Move 1 square and gain 1 mana
    MOVE = "↕"

    # Pay 7 mana to kill at any range.
    # If a player has above 10 mana they must smite on their turn.
    SMITE = "⚡"

    def __str__(self) -> str:
        return f"{self.value} ({self.name.lower()})"


# An action is: use a tile power or a different action
Action = (
    Literal[Tile.FLOWER]
    | Literal[Tile.HOOK]
    | Literal[Tile.BIRD]
    | Literal[Tile.GRENADES]
    | Literal[Tile.KNIVES]
    | OtherAction
)


class GameResult(str, Enum):
    ONGOING = "Ongoing"
    NORTH_WINS = "North Player Wins!"
    SOUTH_WINS = "South Player Wins!"

    # a draw is possible if both players are simultaneously killed by a chromatic grenade
    DRAW = "Draw"


class Response(str, Enum):
    # TODO explain
    # these must match javascript
    ACCEPT = "👍"
    CHALLENGE = "🚩"

    def __str__(self) -> str:
        return f"{self.value} ({self.name.lower()})"


class OutEventType(str, Enum):
    # TODO explain
    # must match javascript

    STATE_CHANGE = "STATE_CHANGE"

    SELECTION_CHANGE = "SELECTION_CHANGE"

    HIGHLIGHT_CHANGE = "HIGHLIGHT_CHANGE"
