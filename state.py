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
# Where S is a tile in play, F is the mana fountain, B and is a Book.

# There are two tiles facedown on each book square.
# when player moves onto a book square & ends their turn on a book square
# they can freely swap those tiles
BOOK_POSITIONS = [Square(2, 0), Square(2, 4)]

# The fountain gives +1 mana when someone moves onto it
FOUNTAIN_POSITION = Square(2, 2)

START_POSITIONS = {
    Player.N: (Square(0, 0), Square(0, 4)),
    Player.S: (Square(4, 0), Square(4, 4))
}


class Tile(Enum):
    """
    The game pieces.

    See actions.py for descriptions and effects.
    """

    FLOWER = "🀥"
    HOOK = "🀍"
    BIRD = "🀐"
    GRENADES = "🀛"
    KNIVES = "🀒"

    # This represents a face-down tile tile, where the value is unknown to a player
    HIDDEN = "🀫"



class Action(IntEnum):
    """
    Each turn, each player chooses one tile in play to take one of these actions.

    Most tiles allow a single action, but Bamboo Knives allows 3,
    so we list them all out separately here.
    """

    # Move 1 square and gain 1 mana
    MOVE = 0

    # Pay 7 mana to kill at any range.
    # If a player has above 10 mana they must smite on their turn.
    SMITE = 1

    # Move 1 and gain 3 mana.
    FLOWER = 2

    # Pull yourself to any enemy & steal 2 mana.
    HOOK = 3

    # Gain 2 mana & move 1-2 squares.
    BIRD = 4

    # spend 3 mana to kill @ range 1
    KNIVES_RANGE_1 = 5

    # spend 5 mana to kill @ range 2
    KNIVES_RANGE_2 = 6

    # target an empty square in a straight line 2 squares away
    # spend 3 mana to kill in a 3x3 square
    GRENADES = 7

# action -> tile enabling that action
# MOVE and SMITE aren't in this dict because they are always enabled
ACTION_TO_TILE = {
    Action.FLOWER: Tile.FLOWER,
    Action.HOOK: Tile.HOOK,
    Action.BIRD: Tile.BIRD,
    Action.KNIVES_RANGE_1: Tile.KNIVES,
    Action.KNIVES_RANGE_2: Tile.KNIVES,
    Action.GRENADES: Tile.GRENADES
}


class Response(IntEnum):
    '''
    A response by the other player to a proposed action.  Only some responses are valid
    on any given move.

    They choices are to accept, challenge, or block
    but when blocking, the player must choose a blocking tile.

    We flatten the choice of blocking tile into a single enum to simplify
    the player input.

    Only some options are valid on any given move.
    '''

    # accept the action as given
    ACCEPT = 0

    # challenge the action
    CHALLENGE = 1

    # block a grappling hook by claiming to have a grappling hook
    BLOCK_WITH_HOOK = 2


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
        - a private state known only to the server that includes all the tiles
        - each player's view on the state where some of the tiles are hidden
    """

    # each player starts with 4 tiles in hand.  They then place 2 on the board.
    # when a player runs out of tiles they lose.
    tiles_in_hand: Dict[Player, List[Tile]]

    # player -> (tile, position of that tile on the board)
    tiles_on_board: Dict[Player, List[Tuple[Tile, Square]]]

    # The two tiles on each book square.
    book_tiles: Dict[Square, Tuple[Tile, Tile]]

    # The remaining tile tiles are hidden off-board and never revealed.
    unused_tiles: List[Tile]

    # The list of tiles that have been revealed when a player lost a life.
    # These tiles stay face-up and are never reshuffled.
    discard: List[Tile]

    # points used to cast tiles
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

    def tiles_here(self) -> Dict[Square, Tile]:
        ''' Square -> the tile occupying that square '''
        return {
            square: tile
            for tile, square in tiles_on_board.values()
        }

    def square_to_player(self) -> Dict[Square, Tile]:
        ''' Square -> the player owning a tile on occupying that square '''
        return {
            square: player
            for player in Player
            for _, square in tiles_on_board[player]
        }


def new_state() -> State:
    """
    Return a new state with the tiles randomly dealt.
    """
    # 3 copies of each tile
    tiles = [tile for tile in Tile for s in range(3) if tile != Tile.HIDDEN]

    # check that we didn't change the count of stuff in the rules and forget to change this method
    assert len(tiles) == 15
    assert len(book_tiles) == 2

    # shuffle, then deal out the cards from fixed indices
    shuffle(tiles)
    return State(
        tiles_in_hand={
            Player.N: tiles[0:4],
            Player.S: tiles[4:8],
        },
        tiles_on_board = {},
        book_tiles={
            BOOK_POSITIONS[0]: (tiles[8], tiles[9]),
            BOOK_POSITIONS[1]: (tiles[10], tiles[11])
        },
        unused_tiles=tiles[12:15],
        discard=[],
        # first player starts with 1 fewer mana
        mana={Player.N: 1, Player.S: 2},
        log=[],
        turn_count = 0
    )


def player_view(private_state: State, player: Player) -> State:
    """
    Return a copy of private_state with all hidden tiles replaced by Tile.HIDDEN

    This represents the player's knowledge of the state.
    """
    opponent = other_player(player)

    # we know the number of tiles in the opponent's hand but not their identity
    opponent_hand = [
        Tile.HIDDEN
        for tile in private_state.tiles_in_hand[opponent]
    ]
    # we know the number and location of tiles on the opponent's board but not their
    # identity
    opponent_board = [
        (Tile.HIDDEN, square)
        for tile, square in private_state.tiles_on_board[opponent]
    ]

    return State(
        tiles_in_hand={
            player: private_state.tiles_in_hand[player],
            opponent: opponent_hand,
        },
        tiles_on_board={
            player: private_state.tiles_on_board[player],
            opponent: opponent_board
        },
        # we can't see the book tiles
        book_tiles={
            Book.W: (Tile.HIDDEN, Tile.HIDDEN),
            Book.E: (Tile.HIDDEN, Tile.HIDDEN),
        },
        # we can't see the unused tiles
        unused_tiles=[Tile.HIDDEN, Tile.HIDDEN, Tile.HIDDEN],
        # we can see everything else
        discard=private_state.discard,
        log=private_state.log,
        turn_count = private_state.turn_count
    )


def check_consistency(private_state: State) -> None:
    """
    Check that the tiles are consistent.
    """

    # check there are exactly 3 of each tile
    tile_counts = {tile: 0 for tile in Tile}
    for tile_list in private_state.tiles_in_hand.values():
        assert 0 <= len(tile_list) <= 2
        for tile in tile_list:
            tile_counts[tile] += 1

    for tile_list in private_state.tiles_on_board.values():
        assert 0 <= len(tile_list) <= 2
        for tile in tile_list:
            tile_counts[tile] += 1

    for tile in private_state.discard:
        tile_counts[tile] += 1

    for tile_1, tile_2 in private_state.book_tiles.values():
        tile_counts[tile_1] += 1
        tile_counts[tile_2] += 1

    assert len(private_state.unused_tiles) == 3
    for tile in private_state.unused_tiles:
        tile_counts[tile] += 1

    for tile in Tile:
        if tile == Tile.HIDDEN:
            assert tile_counts[tile] == 0
        else:
            assert tile_counts[tile] == 3

    # check 0-2 tiles on board and in hand per player
    for player in Player:
        assert 0 <= len(private_state.tiles_in_hand[player]) <= 2
        assert 0 <= len(private_state.tiles_on_board[player]) <= 2
        if len(private_state.tiles_on_board[player]) < 2:
            # tiles in hand should have been exhausted before the player starts
            # losing tiles on board
            assert len(private_state.tiles_in_hand[player]) == 0

    # check tile locations are unique
    assert len(private_state.tiles_here()) == sum(
        len(private_state.tiles_on_board[player])
        for player in Player
    )


def check_game_result(state: State) -> GameResult:
    """
    See if anyone has won the game.
    """
    north_dead = (
        len(tiles_on_board[Player.N]) + len(tiles_in_hand[Player.N]) == 0
    )
    south_dead = (
        len(tiles_on_board[Player.S]) + len(tiles_in_hand[Player.S]) == 0
    )
    if north_dead and south_dead:
        return GameResult.DRAW
    elif south_dead:
        return GameResult.NORTH_WINS
    elif north_dead:
        return GameResult.SOUTH_WINS
    else:
        return GameResult.ONGOING
