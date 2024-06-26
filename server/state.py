from random import shuffle
import random

from pydantic import BaseModel

from server.constants import (
    Player,
    Square,
    GameResult,
    Tile,
    other_player,
)
from server.board import (
    bonus_amount,
    bonus_and_exchange_positions,
    choose_start_positions,
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
    tiles_in_hand: dict[Player, list[Tile]]

    # The tiles in play on the board for each player.
    # See `positions` for the corresponding tile locations.
    tiles_on_board: dict[Player, list[Tile]]

    # Players can see their own tiles and any tile that has been revealed.
    # These correspond to `tiles_on_board`.
    tiles_on_board_revealed: dict[Player, list[bool]]

    # The square of each tile in play on the board for each player.
    # See `tiles_on_board` for the corresponding tile.
    positions: dict[Player, list[Square]]

    # The two tiles on each exchange square.
    # These correspond by index to exchange_positions.
    exchange_tiles: list[list[Tile]]
    exchange_tiles_revealed: dict[Player, list[bool]]

    # The remaining tile tiles are face-down off-board; can be revealed by bird.
    unused_tiles: list[Tile]
    unused_revealed: dict[Player, list[bool]]

    # The list of tiles that have been revealed when a player lost a life.
    # These tiles stay face-up and are never reshuffled.
    discard: list[Tile]

    # points used to cast tiles
    coins: dict[Player, int]

    # human-readable event log of public information
    # TODO: nested indentation?
    # TODO: tag with player so we can color-code them?
    public_log: list[str]

    # current player is the player whose turn it currently is; other_player is the other
    # redundant attributes for easier communication with frontend
    current_player: Player
    other_player: Player

    match_score: dict[Player, int]

    # position of the exchange squares that allow swapping tiles
    exchange_positions: list[Square]

    # Position and value of the bonus square that gives extra + coin
    bonus_position: Square
    bonus_amount: int
    x2_tile: Tile

    game_score: dict[Player, int] = {Player.N: 0, Player.S: 0}

    def tile_at(self, square: Square) -> Tile:
        """The tile occupying on the board at this square.  Error if there isn't one."""
        for player in Player:
            for s, other_square in enumerate(self.positions[player]):
                if other_square == square:
                    return self.tiles_on_board[player][s]
        raise ValueError(f"Expected tile at {square}")

    def reveal_at(self, square: Square) -> None:
        """Reveal the tile at square.  Error if there isn't one."""
        for player in Player:
            for s, other_square in enumerate(self.positions[player]):
                if other_square == square:
                    self.tiles_on_board_revealed[player][s] = True
                    return
        raise ValueError(f"Expected tile at {square}")

    def reveal_unused(self) -> None:
        """Reveal 1 unused tile to current player, or do nothing if they are all revealed."""
        reveal_list = self.unused_revealed[self.current_player]
        if not all(reveal_list):
            next_idx = reveal_list.index(False)
            reveal_list[next_idx] = True

    def player_at(self, square: Square) -> Player:
        """
        The player owning a tile occupying that square. ValueError if there isn't one.
        """
        for player in Player:
            for s, other_square in enumerate(self.positions[player]):
                if other_square == square:
                    return player
        raise ValueError(f"Expected tile at {square}")

    def all_positions(self) -> list[Square]:
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
        # identity; unless they are revealed
        opponent_board = [
            tile if revealed else Tile.HIDDEN
            for tile, revealed in zip(
                self.tiles_on_board[opponent],
                self.tiles_on_board_revealed[opponent],
                strict=True,
            )
        ]

        # we can see exchange tiles if they've been revealed to us
        exchange_tiles = [
            tiles if revealed else [Tile.HIDDEN for _ in tiles]
            for tiles, revealed in zip(
                self.exchange_tiles, self.exchange_tiles_revealed[player], strict=True
            )
        ]

        unused_tiles = [
            tile if revealed else Tile.HIDDEN
            for tile, revealed in zip(
                self.unused_tiles, self.unused_revealed[player], strict=True
            )
        ]

        return State(
            tiles_in_hand={
                player: self.tiles_in_hand[player],
                opponent: opponent_hand,
            },
            tiles_on_board={
                player: self.tiles_on_board[player],
                opponent: opponent_board,
            },
            exchange_tiles=exchange_tiles,
            # all tile positions are public knowledge
            positions=self.positions,
            # we can't see the unused tiles
            unused_tiles=unused_tiles,
            # we can see everything else
            unused_revealed=self.unused_revealed,
            tiles_on_board_revealed=self.tiles_on_board_revealed,
            exchange_tiles_revealed=self.exchange_tiles_revealed,
            discard=self.discard,
            public_log=self.public_log,
            current_player=self.current_player,
            other_player=self.other_player,
            coins=self.coins,
            match_score=self.match_score,
            game_score=self.game_score,
            bonus_position=self.bonus_position,
            bonus_amount=self.bonus_amount,
            x2_tile=self.x2_tile,
            exchange_positions=self.exchange_positions,
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

        for tile_1, tile_2 in self.exchange_tiles:
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
        # TODO
        # assert all(self.coins[player] >= 0 for player in Player)

        assert self.current_player != self.other_player

    def next_turn(self) -> None:
        self.current_player = other_player(self.current_player)
        self.other_player = other_player(self.other_player)

    def score_point(self, player: Player) -> None:
        """Register that a player has scored a point by making a kill."""
        self.game_score[player] += 1
        self.match_score[player] += 1


def new_state(match_score: dict[Player, int]) -> State:
    """
    Return a new state with the tiles randomly dealt.
    """
    # 3 copies of each tile
    tiles: list[Tile] = [tile for tile in Tile for s in range(3) if tile != Tile.HIDDEN]

    # check that we didn't change the count of stuff in the rules and forget to change this method
    assert len(tiles) == 15

    # shuffle, then deal out the cards from fixed indices
    shuffle(tiles)

    bonus_position, exchange_positions = bonus_and_exchange_positions()
    start_positions = choose_start_positions()
    x2_tile = random.choice([t for t in Tile])

    return State(
        tiles_in_hand={
            Player.N: tiles[0:2],
            Player.S: tiles[2:4],
        },
        tiles_on_board={Player.N: tiles[4:6], Player.S: tiles[6:8]},
        tiles_on_board_revealed={Player.N: [False, False], Player.S: [False, False]},
        positions=start_positions,
        exchange_tiles=[
            [tiles[8], tiles[9]],
            [tiles[10], tiles[11]],
        ],
        exchange_tiles_revealed={Player.N: [False, False], Player.S: [False, False]},
        unused_tiles=tiles[12:15],
        unused_revealed={
            Player.N: [False, False, False],
            Player.S: [False, False, False],
        },
        discard=[],
        coins={Player.N: 2, Player.S: 1},
        public_log=[],
        # currently S hardcoded to go first, but N has extra coin
        current_player=Player.S,
        other_player=Player.N,
        match_score=match_score,
        exchange_positions=exchange_positions,
        bonus_position=bonus_position,
        bonus_amount=bonus_amount(),
        x2_tile=x2_tile,
    )
