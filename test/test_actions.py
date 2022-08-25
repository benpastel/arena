from typing import List

from arena.state import State, Wizard, Square
from arena.actions import Action, _all_distances, _grapple_end_square, valid_targets


def test_all_distances():
    # Test case looks like:
    #
    #   . O O
    #   O . X
    #   . O .
    #   . . .
    #
    # where X is the start square and Os are obstructions.

    start = Square(1, 2)
    obstructions = [
        Square(0, 1),
        Square(0, 2),
        Square(1, 0),
        Square(2, 1),
    ]
    dists = _all_distances(start, obstructions, rows=4, cols=3)
    assert dists == {
        start: 0,
        Square(0, 2): 1,
        Square(1, 1): 1,
        Square(2, 2): 1,
        Square(3, 2): 2,
        Square(0, 1): 2,
        Square(1, 0): 2,
        Square(2, 1): 2,
        Square(3, 1): 3,
        Square(3, 0): 4,
        Square(2, 0): 5,
    }


def test_grapple_end_square():
    # north
    assert _grapple_end_square(Square(3, 4), Square(0, 1)) == Square(2, 4)

    # south
    assert _grapple_end_square(Square(3, 4), Square(6, 1)) == Square(4, 4)

    # east
    assert _grapple_end_square(Square(3, 4), Square(4, 7)) == Square(3, 5)

    # west
    assert _grapple_end_square(Square(3, 4), Square(2, 4)) == Square(2, 4)


def test_valid_targets():
    # Test case looks like:
    #
    #   . . . . .
    #   . E . . .
    #   . W . . .
    #   . F E . .
    #   . . . . .
    #
    # Where:
    #   - W is the wizard whose turn it is (SW)
    #   - E is an enemy (NW, NE)
    #   - F is a friend (SE)
    positions = {
        Wizard.SW: Square(2, 1),
        Wizard.SE: Square(3, 1),
        Wizard.NW: Square(1, 1),
        Wizard.NE: Square(3, 2),
    }

    def _assert_targets(action: Action, expected: List[Square]) -> None:
        actual = valid_targets(Wizard.SW, action, positions)
        assert sorted(actual) == sorted(expected), f"{action=}"

    _assert_targets(
        Action.MOVE,
        [
            Square(2, 0),
            Square(2, 2),
        ],
    )
    _assert_targets(
        Action.SMITE,
        [
            Square(1, 1),
            Square(3, 2),
        ],
    )
    _assert_targets(
        Action.FLOWER_POWER,
        [
            Square(2, 0),
            Square(2, 2),
        ],
    )
    _assert_targets(
        Action.GRAPPLING_HOOK,
        [
            Square(1, 1)
            # the other enemy's is an invalid target
            # because their end position is blocked by our friend
        ],
    )
    _assert_targets(
        Action.BIRD_KNIGHT,
        [
            Square(0, 0),
            Square(1, 0),
            Square(2, 0),
            Square(3, 0),
            Square(4, 0),
            Square(0, 2),
            Square(1, 2),
            Square(2, 2),
            Square(1, 3),
            Square(2, 3),
            Square(3, 3),
            Square(2, 4),
        ],
    )
    _assert_targets(Action.BAMBOO_KNIVES_RANGE_1, [Square(1, 1)])
    _assert_targets(Action.BAMBOO_KNIVES_RANGE_2, [Square(3, 2)])
    _assert_targets(
        Action.BAMBOO_KNIVES_RUSH,
        [
            Square(1, 0),
            Square(2, 0),
            Square(3, 0),
            Square(1, 2),
            Square(2, 2),
            Square(2, 3),
        ],
    )
    _assert_targets(
        Action.CHROMATIC_GRENADES,
        [
            Square(2, 3),
        ],
    )
