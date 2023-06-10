"""
Board start positions and randomization.

When randomization is off, we use the default positions.
When randomization is on, we randomize the default positions without their rows.

Default board setup looks like this:

    North Player's Side
         columns
        1 2 3 4 5
       +---------+
     A | |S| |S| |
     B | | | | | |
rows C |E| |B| |E|
     D | | | | | |
     E | |S| |S| |
       +---------+
   South Player's Side

Where S is a tile in play, B is the bonus, E and is a Exchange.
"""
from arena.server.constants import Square, Player

RANDOMIZE_START = False

# There are two tiles facedown on each exchange square.
# when you move onto the square
# they can freely swap those tiles
DEFAULT_EXCHANGE_POSITIONS = [Square(2, 0), Square(2, 4)]

# The bonus gives + coins when a tile ends their movement on it,
# including if they were moved there by an opponent's hook.
DEFAULT_BONUS_POSITION = Square(2, 2)
DEFAULT_BONUS_AMOUNT = 2

DEFAULT_START_POSITIONS = {
    Player.N: (Square(0, 1), Square(0, 3)),
    Player.S: (Square(4, 1), Square(4, 3)),
}

DEFAULT_BONUS_AMOUNT = 2


def bonus_and_exchange_positions() -> tuple[Square, list[Square]]:
    if RANDOMIZE_START:
        assert False
    else:
        return DEFAULT_BONUS_POSITION, DEFAULT_EXCHANGE_POSITIONS


def bonus_amount() -> int:
    if RANDOMIZE_START:
        assert False
    else:
        return DEFAULT_BONUS_AMOUNT


def start_positions() -> dict[Player, tuple[Square, Square]]:
    if RANDOMIZE_START:
        assert False
    else:
        return DEFAULT_START_POSITIONS
