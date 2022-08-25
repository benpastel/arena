from typing import List, Dict
from enum import IntEnum

from arena.state import (
    Spell,
    Wizard,
    State,
    Square,
    ROWS,
    COLUMNS,
    WIZARD_TO_PLAYER,
    PLAYER_TO_WIZARD,
    other_player,
    Player,
)

ALL_SQUARES = [Square(r, c) for r in range(ROWS) for c in range(COLUMNS)]


class Action(IntEnum):
    """
    Each turn, each Wizard takes one of these actions.

    Most spells allow a single action, but Bamboo Knives allows 3,
    so we list them all out separately here.

    TODO: spells will also have "double" versions here where you claim two copies of a tile
    which have a more powerful effect.
    """

    # Move 1 square and gain 1 mana
    MOVE = 0

    # Pay 7 mana to kill at any range.
    # If a Wizard has above 10 mana they must smite on their turn.
    SMITE = 1

    # Move 1 and gain 3 mana.
    FLOWER_POWER = 2

    # Pull any enemy to you & steal 2 mana.
    GRAPPLING_HOOK = 3

    # Gain 1 mana & move 1-3 squares.
    BIRD_KNIGHT = 4

    # spend 3 mana to kill @ range 1
    BAMBOO_KNIVES_RANGE_1 = 5

    # spend 5 mana to kill @ range 2
    BAMBOO_KNIVES_RANGE_2 = 6

    # move 2 in any direction, without gaining any mana
    BAMBOO_KNIVES_RUSH = 7

    # target an empty square in a straight line 2 squares away
    # kill in a 3x3 square
    # RULES: change "empty" definition in google doc
    CHROMATIC_GRENADES = 8


class Response(IntEnum):
    '''
    A response by the other player to a proposed action.  Only some responses are valid
    on any given move.

    They choices are to accept, challenge, or block
    but when blocking, the player must choose a blocking spell.

    We flatten the choice of blocking spell into a single enum to simplify
    the player input.

    Only some options are valid on any given move.
    '''

    # accept the action as given
    ACCEPT = 0

    # challenge the action
    CHALLENGE = 1

    # block a grappling hook by claiming to have a grappling hook
    BLOCK_WITH_GRAPPLING_HOOK = 2

    # block a grappling hook by claiming to have a bird knight
    BLOCK_WITH_BIRD_KNIGHT = 3


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


def _grapple_end_square(start: Square, target: Square) -> Square:
    """
    If `start` grapples `target`, what square do they end up?

    The square adjacent to `start` which is nearest `target`,
    preferring North & South if tied.
    """
    row_diff = target.row - start.row
    col_diff = target.col - start.col

    if row_diff < 0 and abs(row_diff) >= abs(col_diff):
        # North
        return Square(start.row - 1, start.col)
    elif row_diff > 0 and abs(row_diff) >= abs(col_diff):
        # South
        return Square(start.row + 1, start.col)
    elif col_diff > 0:
        # East
        return Square(start.row, start.col + 1)
    elif col_diff < 0:
        # West
        return Square(start.row, start.col - 1)

    raise AssertionError("Above cases should be exhaustive.")


def valid_targets(
    wizard: Wizard, action: Action, wizard_positions: Dict[Wizard, Square]
) -> List[Square]:
    """
    If `wizard` were to take `action` in the current `state`,
    which squares would be valid targets of the action?  E.g. squares the wizard can move
    onto, or squares containing enemy wizards that this wizard can hit with a spell.

    The returned list may be empty, which means the action would be invalid because there is no
    legal target.
    """
    start = wizard_positions[wizard]

    # all other wizards are treated as obstructions for the purposes of calculating range
    obstructions = [s for s in wizard_positions.values() if s != start]
    distances = _all_distances(start, obstructions)

    enemy = other_player(WIZARD_TO_PLAYER[wizard])
    enemy_positions = [wizard_positions[w] for w in PLAYER_TO_WIZARD[enemy]]

    empty_targets = {
        s: dist for s, dist in distances.items() if s not in wizard_positions.values()
    }
    enemy_targets = {s: dist for s, dist in distances.items() if s in enemy_positions}

    if action == Action.MOVE:
        return [s for s, dist in empty_targets.items() if dist == 1]
    elif action == Action.SMITE:
        return list(enemy_targets.keys())
    elif action == Action.FLOWER_POWER:
        return [s for s, dist in empty_targets.items() if dist == 1]
    elif action == Action.GRAPPLING_HOOK:
        # can grapple any enemy
        # unless the square we would pull them into is occupied by someone else
        # RULES: consider forcing target in LOS
        return [
            s
            for s in enemy_targets
            if _grapple_end_square(start, s) not in obstructions
            or _grapple_end_square(start, s) == s
        ]

    elif action == Action.BIRD_KNIGHT:
        return [s for s, dist in empty_targets.items() if 1 <= dist <= 3]
    elif action == Action.BAMBOO_KNIVES_RANGE_1:
        return [s for s, dist in enemy_targets.items() if dist == 1]
    elif action == Action.BAMBOO_KNIVES_RANGE_2:
        return [s for s, dist in enemy_targets.items() if dist == 2]
    elif action == Action.BAMBOO_KNIVES_RUSH:
        return [s for s, dist in empty_targets.items() if 1 <= dist <= 2]
    elif action == Action.CHROMATIC_GRENADES:
        # empty straight line distance 2
        return [
            s
            for s, dist in empty_targets.items()
            if dist == 2 and (s.row == start.row or s.col == start.col)
        ]

    raise ValueError(f"Unknown {action=}")


def take_action(wizard: Wizard, action: Action, state: State) -> None:
    """
    Updates the state with the result of wizard taking action.
    Assumes the action is valid.
    """
    assert False  # TODO
