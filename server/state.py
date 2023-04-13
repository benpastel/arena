from typing import List, Dict, Tuple
from random import shuffle

from pydantic import BaseModel

from arena.server.constants import (
    Player,
    Square,
    GameResult,
    Tile,
    BOOK_POSITIONS,
    BONUS_POSITION,
    other_player,
)


class State(BaseModel):
    """
    The between-turn state of the game (board, tiles, coins, log).

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
    # These correspond by index to book_positions.
    book_tiles: List[Tuple[Tile, Tile]]

    # The remaining tile tiles are hidden off-board and never revealed.
    unused_tiles: List[Tile]

    # The list of tiles that have been revealed when a player lost a life.
    # These tiles stay face-up and are never reshuffled.
    discard: List[Tile]

    # points used to cast tiles
    coins: Dict[Player, int]

    # human-readable event log of public information
    # TODO: nested indentation
    # TODO: tag with player so we can color-code them
    public_log: List[str]

    # current player is the player whose turn it currently is; other_player is the other
    # redundant attributes for easier communication with frontend
    current_player: Player
    other_player: Player

    # position of the book squares that allow swapping tiles
    book_positions: List[Square] = BOOK_POSITIONS

    # Position of the bonus that gives +1 coin
    bonus_position: Square = BONUS_POSITION

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
            # TODO: unless we are standing on the square!
            book_tiles=[
                (Tile.HIDDEN, Tile.HIDDEN),
                (Tile.HIDDEN, Tile.HIDDEN),
            ],
            # we can't see the unused tiles
            unused_tiles=[Tile.HIDDEN, Tile.HIDDEN, Tile.HIDDEN],
            # we can see everything else
            discard=self.discard,
            public_log=self.public_log,
            current_player=self.current_player,
            other_player=self.other_player,
            coins=self.coins,
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

        # check coins non-negative
        assert all(self.coins[player] >= 0 for player in Player)

        assert self.current_player != self.other_player

    def next_turn(self) -> None:
        self.current_player = other_player(self.current_player)
        self.other_player = other_player(self.other_player)

    def score(self) -> Dict[Player, int]:
        """
        The score is how many kills each player has achieved.
        Eventually we'll use this instead of game result for multi-game matches.
        """

        # starting tiles
        # minus opponent's tiles remaining on board
        #   and opponent's tiles remaining in hand
        return {
            player: (
                4
                - len(self.tiles_on_board[other_player(player)])
                - len(self.tiles_in_hand[other_player(player)])
            )
            for player in Player
        }


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
        coins={Player.N: 2, Player.S: 2},
        public_log=[],
        # currently S hardcoded to go first
        current_player=Player.S,
        other_player=Player.N,
    )
