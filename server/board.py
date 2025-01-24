"""
Board start positions and randomization.
"""

import random

from server.constants import Square, Player, COLUMNS, ROWS


RANDOM_BONUS_AMOUNTS = [1, 2, 3]


def bonus_and_exchange_positions() -> tuple[Square, list[Square]]:
    # randomly shuffle the middle squares,
    # then deal them out by index
    squares = [Square(2, c) for c in range(COLUMNS)]
    random.shuffle(squares)
    return squares[0], [squares[1], squares[2]]


def bonus_amount() -> int:
    return random.choice(RANDOM_BONUS_AMOUNTS)


def choose_start_positions() -> dict[Player, list[Square]]:
    # randomly shuffle the column indices for the first and last rows
    # then deal them out by index
    top = [Square(0, c) for c in range(COLUMNS)]
    bottom = [Square(ROWS - 1, c) for c in range(COLUMNS)]
    random.shuffle(top)
    random.shuffle(bottom)
    return {
        Player.N: [top[0], top[1]],
        Player.S: [bottom[0], bottom[1]],
    }
