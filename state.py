from enum import Enum
from typing import Tuple, List, Dict, Literal, NamedTuple
from random import shuffle

from pydantic import BaseModel


# There are two players:
#   North - displayed on top
#   South - displayed on bottom
#
# the enum values must match the javascript & css values
class Player(str, Enum):
    N = "north-player"
    S = "south-player"


def other_player(p: Player) -> Player:
    return Player.S if p == Player.N else Player.N


ROWS = 5
COLUMNS = 5
ROW_NAMES = "ABCDE"


class Square(NamedTuple):
    """A coordinate on the board."""

    row: int
    col: int

    def on_board(self) -> bool:
        """True if the square is in-bounds on the board."""
        return 0 <= self.row < ROWS and 0 <= self.col < COLUMNS

    @classmethod
    def parse(cls, coord_string: str) -> "Square":
        """
        Parse a display-formatted name like B3 -> Square(1, 2)
        """
        assert len(coord_string) == 2
        row = ROW_NAMES.index(coord_string[0])
        col = int(coord_string[1]) - 1  # 0 indexed internally; 1 indexed in UI
        return cls(row, col)

    @classmethod
    def from_list(cls, coords: list) -> "Square":
        assert len(coords) == 2
        row, col = coords
        return cls(row, col)

    def __str__(self) -> str:
        """
        Convert to a display-formatted square name like B3
        """
        row_char = ROW_NAMES[self.row]
        col_char = self.col + 1  # 0 indexed internally; 1 indexed in UI
        return f"{row_char}{col_char}"


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
BOOK_POSITIONS = [Square(2, 0), Square(2, 4)]

# The fountain gives +1 mana when someone moves onto it
FOUNTAIN_POSITION = Square(2, 2)

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
    MOVE = "move"

    # Pay 7 mana to kill at any range.
    # If a player has above 10 mana they must smite on their turn.
    SMITE = "smite"

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


class State(BaseModel):
    """
    This fully represents a game's state.

    There are 3 versions of the state:
        - a private state known only to the server that includes all the tiles
        - each player's view on the state where some of the tiles are hidden
    """

    # Each player starts with 4 tiles in hand.  They then place 2 on the board.
    # When a player runs out of tiles they lose.
    tiles_in_hand: Dict[Player, List[Tile]]

    # The tiles in play on the board for each player.
    # See `positions` for the corresponding tile locations.
    tiles_on_board: Dict[Player, List[Tile]]

    # The square of each tile in play on the board for each player.
    # See `tiles_on_board` for the corresponding tile.
    positions: Dict[Player, List[Square]]

    # The two tiles on each book square.
    # These correspond by position to BOOK_POSITIONS.
    book_tiles: List[Tuple[Tile, Tile]]

    # The remaining tile tiles are hidden off-board and never revealed.
    unused_tiles: List[Tile]

    # The list of tiles that have been revealed when a player lost a life.
    # These tiles stay face-up and are never reshuffled.
    discard: List[Tile]

    # points used to cast tiles
    mana: Dict[Player, int]

    # human-readable event log of public information
    # TODO: nested indentation
    # TODO: tag with player so we can color-code them
    public_log: List[str]

    # count of turns since beginning of game, starting at 0
    turn_count: int

    def current_player(self) -> Player:
        """For now, North is hardcoded to go first."""
        # TODO: change this to a property so it makes it over the wire into javascript
        order = [Player.N, Player.S]
        return order[self.turn_count % 2]

    def other_player(self) -> Player:
        return other_player(self.current_player())

    def tile_at(self, square: Square) -> Tile:
        """The tile occupying on the board at this square.  Error if there isn't one."""
        for player in Player:
            for s, other_square in enumerate(self.positions[player]):
                if other_square == square:
                    return self.tiles_on_board[player][s]
        raise ValueError(f"Expected tile at {square}")

    def player_at(self, square: Square) -> Player:
        """
        The player owning a tile occupying that square. Error if there isn't one.
        """
        for player in Player:
            for s, other_square in enumerate(self.positions[player]):
                if other_square == square:
                    return player
        raise ValueError(f"Expected tile at {square}")

    def all_positions(self) -> List[Square]:
        """All squares with a tile on board, regardless of player"""
        return self.positions[Player.N] + self.positions[Player.S]

    def log(self, msg: str) -> None:
        self.public_log.append(msg)

    def game_result(self) -> GameResult:
        """
        See if anyone has won the game.

        TODO: also draw after x turns
        """
        north_dead = len(self.tiles_on_board[Player.N]) == 0
        south_dead = len(self.tiles_on_board[Player.S]) == 0
        if north_dead and south_dead:
            return GameResult.DRAW
        elif south_dead:
            return GameResult.NORTH_WINS
        elif north_dead:
            return GameResult.SOUTH_WINS
        else:
            return GameResult.ONGOING

    def player_view(self, player: Player) -> "State":
        """
        Return a copy of self with all hidden tiles replaced by Tile.HIDDEN

        This represents the player's knowledge of the state.
        """
        opponent = other_player(player)

        # we know the number of tiles in the opponent's hand but not their identity
        opponent_hand = [Tile.HIDDEN for tile in self.tiles_in_hand[opponent]]
        # we know the number and location of tiles on the opponent's board but not their
        # identity
        opponent_board = [Tile.HIDDEN for tile in self.tiles_on_board[opponent]]

        return State(
            tiles_in_hand={
                player: self.tiles_in_hand[player],
                opponent: opponent_hand,
            },
            tiles_on_board={
                player: self.tiles_on_board[player],
                opponent: opponent_board,
            },
            # all tile positions are public knowledge
            positions=self.positions,
            # we can't see the book tiles
            book_tiles=[
                (Tile.HIDDEN, Tile.HIDDEN),
                (Tile.HIDDEN, Tile.HIDDEN),
            ],
            # we can't see the unused tiles
            unused_tiles=[Tile.HIDDEN, Tile.HIDDEN, Tile.HIDDEN],
            # we can see everything else
            discard=self.discard,
            public_log=self.public_log,
            turn_count=self.turn_count,
            mana=self.mana,
        )

    def check_consistency(self) -> None:
        """
        Check that the tiles are consistent.
        """

        # check there are exactly 3 of each tile
        tile_counts = {tile: 0 for tile in Tile}
        for tile_list in self.tiles_in_hand.values():
            assert 0 <= len(tile_list) <= 2
            for tile in tile_list:
                tile_counts[tile] += 1

        for tile_list in self.tiles_on_board.values():
            assert 0 <= len(tile_list) <= 2
            for tile in tile_list:
                tile_counts[tile] += 1

        for tile in self.discard:
            tile_counts[tile] += 1

        for tile_1, tile_2 in self.book_tiles:
            tile_counts[tile_1] += 1
            tile_counts[tile_2] += 1

        assert len(self.unused_tiles) == 3
        for tile in self.unused_tiles:
            tile_counts[tile] += 1

        for tile in Tile:
            if tile == Tile.HIDDEN:
                assert tile_counts[tile] == 0
            else:
                assert tile_counts[tile] == 3

        # check 0-2 tiles on board and in hand per player
        for player in Player:
            assert 0 <= len(self.tiles_in_hand[player]) <= 2
            assert 0 <= len(self.tiles_on_board[player]) <= 2
            if len(self.tiles_on_board[player]) < 2:
                # tiles in hand should have been exhausted before the player starts
                # losing tiles on board
                assert len(self.tiles_in_hand[player]) == 0

        # check location for each tile on board
        assert all(
            square.on_board()
            for player in Player
            for tile, square in zip(
                self.tiles_on_board[player],
                self.positions[player],
                strict=True,
            )
        )

        # check tile locations are unique
        assert len(self.all_positions()) == len(set(self.all_positions()))

        # check mana non-negative
        assert all(self.mana[player] >= 0 for player in Player)


def new_state() -> State:
    """
    Return a new state with the tiles randomly dealt.
    """
    # 3 copies of each tile
    tiles = [tile for tile in Tile for s in range(3) if tile != Tile.HIDDEN]

    # check that we didn't change the count of stuff in the rules and forget to change this method
    assert len(tiles) == 15
    assert len(BOOK_POSITIONS) == 2

    # shuffle, then deal out the cards from fixed indices
    shuffle(tiles)
    return State(
        tiles_in_hand={
            Player.N: tiles[0:4],
            Player.S: tiles[4:8],
        },
        tiles_on_board={Player.N: [], Player.S: []},
        positions={Player.N: [], Player.S: []},
        book_tiles=[
            (tiles[8], tiles[9]),
            (tiles[10], tiles[11]),
        ],
        unused_tiles=tiles[12:15],
        discard=[],
        # first player starts with 1 fewer mana
        mana={Player.N: 1, Player.S: 2},
        public_log=[],
        turn_count=0,
    )
