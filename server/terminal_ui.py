# Terminal-based UI that I'm gradually migrating to web client

import os
import json
from typing import TypeVar, List, Literal, cast, Optional

from arena.state import (
    GameState,
    START_POSITIONS,
    BOOK_POSITIONS,
    FOUNTAIN_POSITION,
    ROWS,
    ROW_NAMES,
    COLUMNS,
    Player,
)

FOUNTAIN_GLYPH = "+"
BOOK_GLYPH = "#"
EMPTY_SQUARE_GLYPH = " "
MAX_LOGS_TO_DISPLAY = 10


def _clear_terminal() -> None:
    """Clear the terminal on unix-like or Windows systems."""
    os.system("cls||clear")


def _render_hand(player: Player, state: dict) -> str:
    tile_strings = [str(tile) for tile in state["tiles_in_hand"][player]]
    return f"{player}'s hand: {' '.join(tile_strings)}.  {state['mana'][player]} mana"


def display_state(state_json: str) -> None:
    """
    Clear the terminal and display the entire board state, including hands.

    To hide the information a player shouldn't see, pass the result of `player_view()`
    instead of the private state.
    """
    _clear_terminal()

    state = json.loads(state_json)

    board = [[EMPTY_SQUARE_GLYPH for c in range(COLUMNS)] for r in range(ROWS)]

    # add fountains and books first
    for r, c in BOOK_POSITIONS:
        board[r][c] = BOOK_GLYPH

    r, c = FOUNTAIN_POSITION
    board[r][c] = FOUNTAIN_GLYPH

    # add tiles on board, allowing them to cover the books & fountains
    for player in Player:
        for tile, (r, c) in zip(
            state["tiles_on_board"][player], state["positions"][player], strict=True
        ):
            board[r][c] = tile

    column_labels = [str(c + 1) for c in range(COLUMNS)]

    print(_render_hand(Player.N, state))
    print("")
    print("    " + " ".join(column_labels))
    print("   " + "+-" * COLUMNS + "+")
    for r in range(ROWS):
        print(f" {ROW_NAMES[r]} |" + "|".join(board[r]) + "|")
    print("   " + "+-" * COLUMNS + "+")
    print("")
    print(_render_hand(Player.S, state))
    print("")
    for line in state["public_log"][-MAX_LOGS_TO_DISPLAY:]:
        print(f"  - {line}")
    print()


T = TypeVar("T")


def choose_option(
    options: List[T],
    player_view: GameState,
    prompt: str,
) -> T:
    """
    Prompt the player to choose amongst `options` and returns the chosen option.
    """
    display_state(player_view.json())
    print(prompt)
    for t, option in enumerate(options):
        print(f"({t+1}): {option}")

    while True:
        raw_choice = input("> ")
        try:
            choice = int(raw_choice) - 1
            if 0 <= choice < len(options):
                return options[choice]
        except ValueError:
            pass
        # the input was invalid; ask again


def choose_option_or_cancel(
    options: List[T],
    player_view: GameState,
    prompt: str,
) -> Optional[T]:
    """
    Prompt the player to choose amongst `options` or cancel.
    Returns the chosen option or None if they canceled.
    """
    options_or_cancel = cast(List[T | Literal["Cancel"]], options + ["Cancel"])
    choice = choose_option(options_or_cancel, player_view, prompt)
    if choice == "Cancel":
        return None
    else:
        return cast(T, choice)


def place_tiles(player: Player, state: GameState) -> None:
    """
    Prompt the player to choose their starting tiles from their hand.
    """
    assert len(START_POSITIONS[player]) == 2

    for target in START_POSITIONS[player]:
        tile = choose_option(
            state.tiles_in_hand[player],
            state.player_view(player),
            f"Choose a tile to start on {target}",
        )
        state.tiles_in_hand[player].remove(tile)
        state.tiles_on_board[player].append(tile)
        state.positions[player].append(target)


def auto_place_tiles(player: Player, state: GameState) -> None:
    """Arbitrarily place the starting tiles.  For testing."""
    assert len(START_POSITIONS[player]) == 2

    for target in START_POSITIONS[player]:
        tile = state.tiles_in_hand[player][0]
        state.tiles_in_hand[player].remove(tile)
        state.tiles_on_board[player].append(tile)
        state.positions[player].append(target)
