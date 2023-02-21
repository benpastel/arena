from typing import List, Dict
from enum import IntEnum

from arena.state import (
    Tile,
    Wizard,
    State,
    Square,
    ROWS,
    COLUMNS,
    WIZARD_TO_PLAYER,
    PLAYER_TO_WIZARD,
    other_player,
    Player,
    Action,
    Response
)

ALL_SQUARES = [Square(r, c) for r in range(ROWS) for c in range(COLUMNS)]

def _all_distances(
    start: Square,
    obstructions: List[Square],
    rows: int = ROWS,
    cols: int = COLUMNS,
) -> Dict[Square, int]:
    """
    Return the manhattan distance from the start to all squares, with routes:
        - allowed to end on an obstruction
        - not allowed to pass through an obstruction as an intermediate step
    """
    assert start not in obstructions
    assert 0 <= start.row < rows and 0 <= start.col < cols
    assert all(0 <= s.row < rows and 0 <= s.col < cols for s in obstructions)

    explored: Dict[Square, int] = {}

    to_explore = [start]
    to_explore_dists = [0]

    while to_explore:
        s = to_explore.pop(0)
        dist = to_explore_dists.pop(0)
        explored[s] = dist
        if s in obstructions:
            continue
        for r, c in [
            (s.row - 1, s.col),
            (s.row + 1, s.col),
            (s.row, s.col - 1),
            (s.row, s.col + 1),
        ]:
            if 0 <= r < rows and 0 <= c < cols and Square(r, c) not in explored:
                to_explore.append(Square(r, c))
                to_explore_dists.append(dist + 1)
    return explored


def _grapple_end_square(
    start: Square,
    target: Square,
    obstructions: List[Square]
) -> Optional[Square]:
    """
    If `start` grapples `target`, what square do they end up?

    Return the square adjacent to `start` which is nearest `target`.

    Return None if the grapple is illegal.  Grapples are in straight lines or
    diagonals (like a chess Queen) and blocked by other players.
    """
    row_diff = target.row - start.row
    col_diff = target.col - start.col

    if not (
        row_diff == 0 and col_diff != 0
        or row_diff != 0 and col_diff == 0
        or row_diff == col_diff
    ):
        # not in a straight line / diagonal
        return None

    # which direction is a single step from start towards target?
    row_step = row_diff / abs(row_diff) if row_diff != 0 else 0
    col_step = col_diff / abs(col_diff) if col_diff != 0 else 0
    assert row_step != 0 or col_step != 0

    current_square = start
    while True:
        next_square = Square(
            row=current_square.row + row_step,
            col=current_square.col + col_step
        )
        # should never walk off board without hitting target
        assert 0 <= next_square.row < ROWS
        assert 0 <= next_square.col < COLUMNS

        if next_square == target:
            # this is the final square before target
            return current_square

        if next_square in obstructions:
            # we hit an obstruction first; this is not a legal move
            return None

        current_square = next_square


def valid_targets(
    start: Square, action: Action, state: State
) -> Dict[Action, List[Square]]:
    """
    If the tile on `start` were to take `action` in the current `state`,
    which squares would be valid targets of the action?  E.g. squares the tile can move
    onto, or squares containing enemy tiles that this tile can hit.

    The returned list may be empty, which means the action would be invalid because there
    is no legal target.

    TODO: LEFT OFF HERE
    just had the idea of redefining this as a dict Action -> List[Square]
    so we can see the full list of valid actions based on mana AND obstructions
    e.g. if mana > 10 you must smite and nothing else is valid
    this should simplify the game loop

    (also just redefined action type)
    """

    # all other tiles are obstructions that block line of site
    # TODO grenades not blocked by LOS
    obstructions = [s for s in state.all_positions() if s != start]
    distances = _all_distances(start, obstructions)

    mana = state.mana[state.current_player()]

    enemy_positions = state.positions[state.other_player()]

    empty_targets = {
        s: dist for s, dist in distances.items() if s not in obstructions
    }
    enemy_targets = {s: dist for s, dist in distances.items() if s in enemy_positions}

    if action == OtherAction.MOVE:
        return [s for s, dist in empty_targets.items() if dist == 1]
    elif action == OtherAction.SMITE:
        if mana >= 7:

        return list(enemy_targets.keys())
    elif action == Tile.FLOWER:
        return [s for s, dist in empty_targets.items() if dist == 1]
    elif action == Tile.HOOK:
        return [
            s
            for s in enemy_targets
            if _grapple_end_square(start, s, obstructions)
        ]

    elif action == Tile.BIRD:
        return [s for s, dist in empty_targets.items() if 1 <= dist <= 3]
    elif action == Tile.KNIVES:
        return [s for s, dist in enemy_targets.items() if dist == 1]
    elif action == Action.KNIVES_RANGE_2:
        return [s for s, dist in enemy_targets.items() if dist == 2]
    elif action == Action.KNIVES_RUSH:
        return [s for s, dist in empty_targets.items() if 1 <= dist <= 2]
    elif action == Action.GRENADES:
        # grenades do not require line of sight
        # they require an empty square at distance exactly 2
        return [
            s
            for s, dist in empty_targets.items()
            if dist == 2 and (s.row == start.row or s.col == start.col)
        ]

    raise ValueError(f"Unknown {action=}")


def tile_for_action(action: Action) -> Tile:



def take_action(wizard: Wizard, action: Action, state: State) -> None:
    """
    Updates the state with the result of wizard taking action.
    Assumes the action is valid.
    """
    assert False  # TODO
