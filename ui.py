from typing import TypeVar

from arena.state import (
    State,
    Tile,
    BOOK_POSITIONS,
    FOUNTAIN_POSITIONS,
    ROWS,
    COLUMNS,
)

FOUNTAIN_GLYPH = "✨"
BOOK_GLYPH = "📖"
EMPTY_SQUARE_GLYPH = "  "  # two spaces matches unicode display width on my termina

def _render_hand(player: Player, state: State) -> str:
    return f"{player}'s hand: {state.tiles_in_hand[player].join(" ")}"

def display_state(state: State) -> None:
    board = [[EMPTY_SQUARE_GLYPH for c in range(COLUMNS)] for r in range(ROWS)]

    # add fountains and books first
    for r, c in BOOK_POSITIONS.values():
        board[r][c] = BOOK_GLYPH

    for r, c in FOUNTAIN_POSITIONS:
        board[r][c] = FOUNTAIN_GLYPH

    # add tiles on board, allowing them to cover the books & fountains
    for player in Player:
        for tile, (r, c) in zip(
            state.tiles_on_board[player],
            state.positions[player],
            strict=True
        ):
            board[r][c] = tile.value

    print(_render_hand(Player.N), state)
    print("")
    print("  " + "+--" * COLUMNS + "+")
    for r in range(ROWS):
        print("  |" + "|".join(board[r]) + "|")
    print("  " + "+--" * COLUMNS + "+")
    print("")
    print(_render_hand(Player.S), state)


T = TypeVar('T')
def choose_option(
    options: List[T],
    player_view: State,
    prompt: str,
) -> T:
    """
    Prompt the player to choose amongst `options` and returns the chosen option.
    """
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


''' Special option indicating the player wants to cancel previous selections. '''
CANCEL = "Cancel"


def choose_option_or_cancel(
    options: List[T],
    player_view: State,
    prompt: str,
) -> T | Literal[CANCEL]:
    """
    Prompt the player to choose amongst `options` or cancel.
    Returns the chosen option or None if they canceled.
    """
    options_or_cancel: List[T | Literal[Cancel]] = [options] + [CANCEL]
    return choose_option(options_or_cancel, player_view, prompt)


def place_tiles(player: Player, state: State) -> None:
    '''
    Choose which tiles start on the board.
    '''
    assert len(START_POSITIONS[player]) == 2

    # choose in a loop to enable canceling
    while True:
        first_position = START_POSITIONS[player][0]
        first_tile = choose_option(
            state.tiles_in_hand[player],
            player_view(player, state),
            f"Choose a tile to start on {first_position}",

        # TODO left off here


    assert False, "TODO"

