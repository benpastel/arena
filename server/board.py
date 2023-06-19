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
import random

from server.constants import Square, Player, COLUMNS, ROWS

# TODO: set this as a URL option or something?
# eventually table option
RANDOMIZE_START = True

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

RANDOM_BONUS_AMOUNTS = [2]


def bonus_and_exchange_positions() -> tuple[Square, list[Square]]:
    if not RANDOMIZE_START:
        return DEFAULT_BONUS_POSITION, DEFAULT_EXCHANGE_POSITIONS

    # randomly shuffle the middle squares,
    # then deal them out by index
    squares = [Square(2, c) for c in range(COLUMNS)]
    random.shuffle(squares)
    return squares[0], [squares[1], squares[2]]


def bonus_amount() -> int:
    if RANDOMIZE_START:
        return random.choice(RANDOM_BONUS_AMOUNTS)
    else:
        return DEFAULT_BONUS_AMOUNT


def start_positions() -> dict[Player, tuple[Square, Square]]:
    if not RANDOMIZE_START:
        return DEFAULT_START_POSITIONS

    # randomly shuffle the column indices for the first and last rows
    # then deal them out by index
    top = [Square(0, c) for c in range(COLUMNS)]
    bottom = [Square(ROWS - 1, c) for c in range(COLUMNS)]
    random.shuffle(top)
    random.shuffle(bottom)
    return {
        Player.N: (top[0], top[1]),
        Player.S: (bottom[0], bottom[1]),
    }
