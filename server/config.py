"""
Board start positions and randomization.
"""

import random

from server.constants import Square, Player, COLUMNS, ROWS, Tile

# how much extra $ do you get from sitting on the bonus square, randomized per game
POSSIBLE_BONUS_AMOUNTS = [1, 2, 3]
DEFAULT_BONUS_AMOUNT = 2

# how many unused cards are revealed per-turn from the bonus square, randomized per game
POSSIBLE_BONUS_REVEALS = [0, 1, 2, 3]
DEFAULT_BONUS_REVEAL = 1

# how much $ it costs to smite, randomized per game
POSSIBLE_SMITE_COSTS = [8, 9, 10, 11, 12]
DEFAULT_SMITE_COST = 10

# how much $ each player starts with, randomized per game
POSSIBLE_START_COINS = [0, 1, 2, 3, 4]
DEFAULT_START_COINS = 2

# can you go into debt via HOOK?
NEGATIVE_COINS_OK = True

# possible tiles in the game, randomized per game
# ordered in increasing complexity, for a better learning curve when first reading the tooltips
POSSIBLE_TILES = [
    Tile.FLOWER,
    Tile.HARVESTER,
    Tile.BIRD,
    Tile.KNIVES,
    Tile.THIEF,
    Tile.FIREBALL,
    Tile.BACKSTABBER,
    Tile.GRENADES,
    Tile.HOOK,
    Tile.RAM,
]
DEFAULT_TILES = [
    Tile.HARVESTER,
    Tile.KNIVES,
    Tile.FIREBALL,
    Tile.BACKSTABBER,
    Tile.HOOK,
]


def bonus_and_exchange_positions() -> tuple[Square, list[Square]]:
    # Always randomized.
    # randomly shuffle the middle squares,
    # then deal them out by index
    squares = [Square(2, c) for c in range(COLUMNS)]
    random.shuffle(squares)
    return squares[0], [squares[1], squares[2]]


def choose_bonus_amount(randomize: bool) -> int:
    if randomize:
        return random.choice(POSSIBLE_BONUS_AMOUNTS)
    else:
        return DEFAULT_BONUS_AMOUNT


def choose_bonus_reveal(randomize: bool) -> int:
    if randomize:
        return random.choice(POSSIBLE_BONUS_REVEALS)
    else:
        return DEFAULT_BONUS_REVEAL


def choose_smite_cost(randomize: bool) -> int:
    if randomize:
        return random.choice(POSSIBLE_SMITE_COSTS)
    else:
        return DEFAULT_SMITE_COST


def choose_start_coins(randomize: bool) -> int:
    if randomize:
        return random.choice(POSSIBLE_START_COINS)
    else:
        return DEFAULT_START_COINS


def choose_start_positions() -> dict[Player, list[Square]]:
    # Always randomized.
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


def choose_tiles_in_game(randomize: bool) -> list[Tile]:
    if randomize:
        # choose 5 tiles at random
        # preserve the original ordering, which is ordered in increasing complexity
        # for a better learning curve when first reading the tooltips
        random_indices = random.sample(range(len(POSSIBLE_TILES)), 5)
        random_indices = sorted(random_indices)
        return [POSSIBLE_TILES[i] for i in random_indices]
    else:
        return DEFAULT_TILES
