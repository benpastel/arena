from typing import List, Dict, Optional

from arena.server.state import State
from arena.server.constants import (
    Square,
    Action,
    OtherAction,
    Tile,
    ROWS,
    COLUMNS,
)


"""Money gains & costs"""
COIN_GAIN = {
    OtherAction.MOVE: 1,
    Tile.BIRD: 2,
    Tile.FLOWER: 3,
}
SMITE_COST = 7
GRENADES_COST = 3
KNIVES_RANGE_1_COST = 3
KNIVES_RANGE_2_COST = 5
GRAPPLE_STEAL_AMOUNT = 2
MUST_SMITE_AT = 10


def _all_distances(
    start: Square,
    obstructions: List[Square],
    rows: int = ROWS,
    cols: int = COLUMNS,
) -> Dict[Square, int]:
    """
    Return the distance from the start to all squares, with routes:
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
        if s in explored:
            continue

        explored[s] = dist

        if s in obstructions:
            continue

        for r, c in [
            (s.row - 1, s.col - 1),
            (s.row - 1, s.col + 0),
            (s.row - 1, s.col + 1),
            (s.row + 0, s.col - 1),
            (s.row + 0, s.col + 1),
            (s.row + 1, s.col - 1),
            (s.row + 1, s.col + 0),
            (s.row + 1, s.col + 1),
        ]:
            if 0 <= r < rows and 0 <= c < cols and Square(row=r, col=c) not in explored:
                to_explore.append(Square(row=r, col=c))
                to_explore_dists.append(dist + 1)
    return explored


def _manhattan_dist(s1: Square, s2: Square) -> int:
    return abs(s1.row - s2.row) + abs(s1.col - s2.col)


def _grapple_end_square(
    start: Square, target: Square, obstructions: List[Square]
) -> Optional[Square]:
    """
    If the grapple is valid, return the square the enemy is pulled to.
    Otherwise return None.

    A grapple is valid if the target is a Queen move away (straight line or diagonal)
    and the enemy is in line of sight.

    The end square is the square adjacent to `start` which is nearest to `target` -
    i.e. the first square along the line of sight.
    """
    row_diff = target.row - start.row
    col_diff = target.col - start.col

    if not (
        row_diff == 0
        and col_diff != 0
        or row_diff != 0
        and col_diff == 0
        or abs(row_diff) == abs(col_diff)
    ):
        # not in a straight line / diagonal
        return None

    # which direction is a single step from start towards target?
    row_step = row_diff // abs(row_diff) if row_diff != 0 else 0
    col_step = col_diff // abs(col_diff) if col_diff != 0 else 0
    assert row_step != 0 or col_step != 0

    end_square = Square(row=start.row + row_step, col=start.col + col_step)

    # walk through the path and make sure no obstructions
    current_square = start
    while True:
        next_square = Square(
            row=current_square.row + row_step, col=current_square.col + col_step
        )
        # should never walk off board without hitting target
        assert 0 <= next_square.row < ROWS
        assert 0 <= next_square.col < COLUMNS

        if next_square == target:
            # this is the final square before target
            return end_square

        if next_square in obstructions:
            # we hit an obstruction first; this is not a legal move
            return None

        current_square = next_square


def _grenade_hits(center: Square, positions: List[Square]) -> List[Square]:
    """
    Return a possibly-empty list of tile positions hit by the grenade.

    Grenades hit a 3x3 area centered on `center`.
    """
    return [
        hit
        for hit in positions
        if abs(center.row - hit.row) <= 1 and abs(center.col - hit.col) <= 1
    ]


def _grenade_targets(
    start: Square, all_positions: List[Square], enemy_positions: List[Square]
) -> List[Square]:
    """
    Return a possibly-empty list of valid squares to target a grenade.

    Grenades can be thrown exactly 2 squares in a cardinal direction onto an empty square.
    They ignore LOS (i.e. they can go over obstructions).

    For now we restrict to squares that hit at least one enemy to reduce misclicks.
    """
    assert len(enemy_positions) > 0
    assert all(e in all_positions for e in enemy_positions)

    # start with the empty squares at range
    potential_targets = [
        t
        for t in [
            Square(start.row + 2, start.col),
            Square(start.row - 2, start.col),
            Square(start.row, start.col + 2),
            Square(start.row, start.col - 2),
        ]
        if t.on_board() and not t in all_positions
    ]

    # filter to ones that hit at least one enemy
    return [
        target
        for target in potential_targets
        if any(hit in enemy_positions for hit in _grenade_hits(target, all_positions))
    ]


def valid_targets(start: Square, state: State) -> Dict[Action, List[Square]]:
    """
    What are the valid actions for the current player from the start square,
    and what squares are those actions allowed to target?

    The square lists will be non-empty; if an action has no valid target, then
    it's not currently a valid action.
    """

    # all other tiles are obstructions that block line of site
    obstructions = [s for s in state.all_positions() if s != start]
    distances = _all_distances(start, obstructions)

    coins = state.coins[state.current_player]

    enemy_positions = state.positions[state.other_player]

    empty_targets = {s: dist for s, dist in distances.items() if s not in obstructions}
    enemy_targets = {s: dist for s, dist in distances.items() if s in enemy_positions}

    # there must be enemies or the game would have ended
    assert len(enemy_targets) > 0

    if coins >= MUST_SMITE_AT:
        # smiting is the only valid action
        return {OtherAction.SMITE: list(enemy_targets.keys())}

    # move, FLOWER, and BIRD cost no coins
    # and move to any empty square at some distance
    #
    # for now we'll allow empty lists when there is no valid target square;
    # we'll drop those keys at the end
    actions: Dict[Action, List[Square]] = {
        OtherAction.MOVE: [s for s, dist in empty_targets.items() if dist == 1],
        Tile.FLOWER: [s for s, dist in empty_targets.items() if dist == 1],
        Tile.BIRD: [s for s, dist in empty_targets.items() if 1 <= dist <= 2],
    }

    # see `_grapple_end_square` for the definition of valid grapple targets
    actions[Tile.HOOK] = [
        s for s in enemy_targets if _grapple_end_square(start, s, obstructions)
    ]

    if coins >= SMITE_COST:
        # can smite any enemy
        actions[OtherAction.SMITE] = list(enemy_targets.keys())

    if coins >= KNIVES_RANGE_2_COST:
        actions[Tile.KNIVES] = [
            s for s in enemy_targets if 1 <= _manhattan_dist(start, s) <= 2
        ]
    elif coins >= KNIVES_RANGE_1_COST:
        actions[Tile.KNIVES] = [
            s for s in enemy_targets if 1 == _manhattan_dist(start, s)
        ]

    if coins >= GRENADES_COST:
        # see `_grenade_targets` for the definition of valid grenade targets
        actions[Tile.GRENADES] = _grenade_targets(start, obstructions, enemy_positions)

    # drop actions with no valid targets
    return {a: targets for a, targets in actions.items() if len(targets) > 0}


def take_action(
    start: Square, action: Action, target: Square, state: State
) -> List[Square]:
    """
    Updates the state with the result of the action.
    Assumes the action is valid.

    Returns a possibly-empty list of casualties (positions of tiles that got killed)

    TODO: this will need to split into:
        - hits (informational-only)
        - take action (effect-only)

    or both together but switched via flag
    """
    player = state.current_player
    enemy = state.other_player

    if action in (OtherAction.MOVE, Tile.FLOWER, Tile.BIRD):
        # move to the target square
        state.positions[player].remove(start)
        state.positions[player].append(target)

        # gain coins
        state.coins[player] += COIN_GAIN[action]

        # kill nobody
        return []

    if action == Tile.HOOK:
        # move target next to us
        end_square = _grapple_end_square(start, target, obstructions=[])
        assert end_square
        state.positions[enemy].remove(target)
        state.positions[enemy].append(end_square)

        # steal
        steal_amount = min(GRAPPLE_STEAL_AMOUNT, state.coins[enemy])
        state.coins[player] += steal_amount
        state.coins[enemy] -= steal_amount

        # kill noboby
        return []

    if action == OtherAction.SMITE:
        # pay cost
        state.coins[player] -= SMITE_COST

        # kill target
        return [target]

    if action == Tile.GRENADES:
        # pay cost
        state.coins[player] -= GRENADES_COST

        # see `_grenate_hits` for definition of who dies
        return _grenade_hits(target, state.all_positions())

    if action == Tile.KNIVES:
        # cost depends on distance to target
        dist = max(abs(start.row - target.row), abs(start.col - target.col))
        if dist == 2:
            state.coins[player] -= KNIVES_RANGE_2_COST
        else:
            assert dist == 1
            state.coins[player] -= KNIVES_RANGE_1_COST

        # kill target
        return [target]

    assert False, f"unknown {action=}"
