from arena.state import (
    State,
    Tile,
    Wizard,
    BOOK_POSITIONS,
    SPARKLE_POSITIONS,
    ROWS,
    COLUMNS,
)

WIZARD_GLYPHS = {
    Wizard.NW: "🧙🏿‍♂️",
    Wizard.NE: "🧙🏻‍♂️",
    Wizard.SW: "🧙🏿‍♀️",
    Wizard.SE: "🧙🏻‍♀️",
}

SPELL_GLYPHS = {
    Tile.FLOWER: "🀥",
    Tile.HOOK: "🀍",
    Tile.BIRD: "🀐",
    Tile.GRENADES: "🀛",
    Tile.KNIVES: "🀒",
    Tile.HIDDEN: "🀫",
}
SPARKLE_GLYPH = "✨"
BOOK_GLYPH = "📖"
EMPTY_SQUARE_GLYPH = "  "  # two spaces matches unicode display width on my terminal


def _render_tiles(wizard: Wizard, state: State) -> str:
    # TODO update
    wizard_glyph = WIZARD_GLYPHS[wizard]
    tile_glyphs = [SPELL_GLYPHS[s] for s in state.wizard_tiles[wizard]]
    return f'{wizard_glyph}: {" ".join(tile_glyphs)}'


def display_state(state: State) -> None:
    # TODO update
    board = [[EMPTY_SQUARE_GLYPH for c in range(COLUMNS)] for r in range(ROWS)]

    # add sparkles and books first
    for r, c in BOOK_POSITIONS.values():
        board[r][c] = BOOK_GLYPH

    for r, c in SPARKLE_POSITIONS:
        board[r][c] = SPARKLE_GLYPH

    # add wizards, allowing them to cover the books & sparkles
    for wizard, (r, c) in state.wizard_positions.items():
        board[r][c] = WIZARD_GLYPHS[wizard]

    print(f"{_render_tiles(Wizard.NW, state):16}{_render_tiles(Wizard.NE, state):16}")
    print("")
    print("  " + "+--" * COLUMNS + "+")
    for r in range(ROWS):
        print("  |" + "|".join(board[r]) + "|")
    print("  " + "+--" * COLUMNS + "+")
    print("")
    print(f"{_render_tiles(Wizard.SW, state):16}{_render_tiles(Wizard.SE, state):16}")


def place_tiles(player: Player, state: State) -> None:
    assert False, "TODO"


def choose_square(
    options: List[Square],
    player_view: State,
    prompt: str,
    allow_cancel: bool
) -> Optional[Square]:
    assert False, "TODO"


def choose_action(
    options: List[Action],
    player_view: State,
    prompt: str,
    allow_cancel: bool
) -> Optional[Action]:
    assert False, "TODO"


def choose_tile(
    options: List[Tile],
    player_view: State,
    prompt: str,
    allow_cancel: bool
) -> Optional[Tile]:
    assert False, "TODO"
