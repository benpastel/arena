from enum import IntEnum

from arena.game import (
    Spell,
    Wizard,
    State,
    Square,
    ROWS,
    COLUMNS,
    WIZARD_TO_PLAYER,
    other_player,
    Player
)
ALL_SQUARES = [Square(r, c) for r in range(ROWS) for c in range(COLUMNS)]


class Action(IntEnum):
    '''
    Each turn, each Wizard takes one of these actions.

    Most spells allow a single action, but Bamboo Knives allows 3,
    so we list them all out separately here.

    TODO: spells will also have "double" versions here where you claim two copies of a tile
    which have a more powerful effect.
    '''

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


def _all_distances(start: Square, obstructions: List[Square]) -> Dict[Square, int]:
    '''
    Return the manhattan distance from the start to all squares, with routes:
        - allowed to end on an obstruction
        - not allowed to pass through an obstruction as an intermediate step

    TODO test this next!
    '''
    assert start not in obstructions

    explored: Dict[Square, int] = {}

    # (square to explore, that square's distance from start)
    to_explore = {start: 0}

    while to_explore:
        s, dist = to_explore.pop()
        explored[s] = dist
        if s not in obstructions:
            to_explore += [
                (Square(r, c), dist + 1)
                for r in range(s.row - 1, s.row + 2)
                for c in range(s.col - 1, s.col + 2)
                if 0 <= r < ROWS
                and 0 <= c < COLS
                and Square(r, c) not in explored
            ]
    return explored


def _empty(s: Square, state: State) -> bool:
    '''
    True if no wizard is on the square.
    '''
    return s not in wizard_positions.values()


def _has_enemy(s: Square, wizard: Wizard, state: State) -> bool:
    '''
    True if an enemy of `wizard` is on the square.
    '''


    return s in enemy_positions


def valid_targets(wizard: Wizard, action: Action, state: State) -> List[Square]:
    '''
    If `wizard` were to take `action` in the current `state`,
    which squares would be valid targets of the action?  E.g. squares the wizard can move
    onto, or squares containing enemy wizards that this wizard can hit with a spell.

    The returned list may be empty, which means the action would be invalid because there is no
    legal target.
    '''
    start = state.wizard_positions[wizard]

    # all other wizards are treated as obstructions for the purposes of calculating range
    obstructions = [s for s in state.wizard_positions.values() if s != start]
    distances = _all_distances(start, obstructions)

    enemy = other_player(WIZARD_TO_PLAYER[wizard])
    enemy_positions = [wizard_positions[w] for w in PLAYER_TO_WIZARD[enemy]]

    empty_targets = {
        s: dist
        for s, dist in distances
        if s not in state.wizard_positions
    }
    enemy_targets = {
        s: dist
        for s, dist in distances
        if s in enemy_positions
    }

    if action == Action.MOVE:
        return [
            s
            for s, dist in empty_targets
            if dist == 1
        ]
    # TODO: left off here: refactor all to use the lists above

    elif action == Action.SMITE:
        return _enemy_positions(us, max_dist = ROWS * COLUMNS)
    elif action == Action.GRAPPLING_HOOK:
        return [
            s for s in ALL_SQUARES
            if _dist(us, s) > 0
            and _has_enemy(s)
        ]
    elif action == Action.BIRD_KNIGHT:
        return [
            s for s in ALL_SQUARES
            if 1 <= _dist(us, s) <= 3
            and _empty(s)
        ]
    elif action == Action.BAMBOO_KNIVES_RANGE_1:
        return [
            s for s in ALL_SQUARES
            if _dist(us, s) == 1
            and _has_enemy(s)
        ]
    elif action == Action.BAMBOO_KNIVES_RANGE_2:
        return [
            s for s in ALL_SQUARES
            if _dist(us, s) == 2
            and _has_enemy(s)
        ]
    elif action == Action.BAMBOO_KNIVES_RUSH:
        return [
            s for s in ALL_SQUARES

            and
        ]


    assert False # TODO



def take_action(wizard: Wizard, action: Action, state: State) -> None:
    '''
    Updates the state with the result of wizard taking action.
    Assumes the action is valid.
    '''
    assert False # TODO








