from arena.state import State, Wizard
from arena.actions import Action, _all_distances, _grapple_end_square, valid_targets


def test_all_distances():
    # Test case looks like:
    #
    #   . O .
    #   O . X
    #   . O .
    #   . . .
    #
    # where X is the start square and Os are obstructions.

    start = Square(1, 2)
    obstructions = [
        Square(0, 1),
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
        Square(3, 1): 3,
        Square(3, 0): 4,
        Square(2, 0): 5,
    }


def test_grapple_end_square():
    assert False, "TODO"


def test_valid_targets():
    assert False, "TODO"
