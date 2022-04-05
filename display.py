from state import State, Spell, Wizard, BOOK_POSITIONS, SPARKLE_POSITIONS, ROWS, COLUMNS

WIZARD_GLYPHS = {
    Wizard.NW: '🧙🏿‍♂️',
    Wizard.NE: '🧙🏻‍♂️',
    Wizard.SW: '🧙🏿‍♀️',
    Wizard.SE: '🧙🏻‍♀️',
}

SPELL_GLYPHS = {
    Spell.FLOWER_POWER: '🀥',
    Spell.GRAPPLING_HOOK: '🀍',
    Spell.BIRD_KNIGHT: '🀐',
    Spell.CHROMATIC_GRENADES: '🀛',
    Spell.BAMBOO_KNIVES: '🀒',
    Spell.HIDDEN: '🀫'
}
SPARKLE_GLYPH = '✨'
BOOK_GLYPH = '📖'
EMPTY_SQUARE_GLYPH = '  ' # two spaces matches unicode display width on my terminal

def _render_tiles(wizard: Wizard, state: State) -> str:
    wizard_glyph = WIZARD_GLYPHS[wizard]
    spell_glyphs = [SPELL_GLYPHS[s] for s in state.wizard_spells[wizard]]
    return f'{wizard_glyph}: {" ".join(spell_glyphs)}'

def print_state(state: State) -> None:
    board = [[EMPTY_SQUARE_GLYPH for c in range(COLUMNS)] for r in range(ROWS)]

    # add sparkles and books first
    for r, c in BOOK_POSITIONS.values():
        board[r][c] = BOOK_GLYPH

    for r, c in SPARKLE_POSITIONS:
        board[r][c] = SPARKLE_GLYPH

    # add wizards, allowing them to cover the books & sparkles
    for wizard, (r, c) in state.wizard_positions.items():
        board[r][c] = WIZARD_GLYPHS[wizard]

    print(f'{_render_tiles(Wizard.NW, state):16}{_render_tiles(Wizard.NE, state):16}')
    print('')
    print('  ' + '+--' * COLUMNS + '+')
    for r in range(ROWS):
        print('  |' + '|'.join(board[r]) + '|')
    print('  ' + '+--' * COLUMNS + '+')
    print('')
    print(f'{_render_tiles(Wizard.SW, state):16}{_render_tiles(Wizard.SE, state):16}')



