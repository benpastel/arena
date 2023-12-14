from ..server.state import Square
from ..server.actions import _all_distances


def test_all_distances():
    # Test case looks like:
    #
    #   . O O
    #   O . X
    #   . O .
    #   . . .
    #
    # where X is the start square and Os are obstructions.

    # TODO: update to non-manhattan distances

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
        Square(2, 1): 1,
        Square(0, 1): 1,
        Square(0, 0): 2,
        Square(1, 0): 2,
        Square(3, 1): 2,
        Square(3, 2): 2,
        Square(2, 0): 2,
        Square(3, 0): 3,
    }


# TODO finish this test at some point
# def test_valid_targets():
#     # Test board looks like:
#     #      1 2 3 4 5
#     # A |  . F . . .
#     # B |  . E . . .
#     # C |  . S . . E
#     # D |  . F F . .
#     # E |  . . . . .
#     #
#     # Where:
#     #   - S is the start square
#     #   - E is an enemy tile (Player.S)
#     #   - F is a friendly tile (Player.N)
#     s_positions = [

#     ]

#     state = State(
#         turn_count = 0,
#         positions = {Player.N: [Square(


#     )

#     def _assert_targets(action: Action, expected: list[Square]) -> None:
#         actual = valid_targets(Wizard.SW, action, positions)
#         assert sorted(actual) == sorted(expected), f"{action=}"

#     _assert_targets(
#         Action.MOVE,
#         [
#             Square(2, 0),
#             Square(2, 2),
#         ],
#     )
#     _assert_targets(
#         Action.SMITE,
#         [
#             Square(1, 1),
#             Square(3, 2),
#         ],
#     )
#     _assert_targets(
#         Action.FLOWER,
#         [
#             Square(2, 0),
#             Square(2, 2),
#         ],
#     )
#     _assert_targets(
#         Action.GRAPPLING_HOOK,
#         [
#             Square(1, 1)
#             # the other enemy's is an invalid target
#             # because their end position is blocked by our friend
#         ],
#     )
#     _assert_targets(
#         Action.BIRD,
#         [
#             Square(0, 0),
#             Square(1, 0),
#             Square(2, 0),
#             Square(3, 0),
#             Square(4, 0),
#             Square(0, 2),
#             Square(1, 2),
#             Square(2, 2),
#             Square(1, 3),
#             Square(2, 3),
#             Square(3, 3),
#             Square(2, 4),
#         ],
#     )
#     _assert_targets(Action.KNIVES_RANGE_1, [Square(1, 1)])
#     _assert_targets(Action.KNIVES_RANGE_2, [Square(3, 2)])
#     _assert_targets(
#         Action.KNIVES_RUSH,
#         [
#             Square(1, 0),
#             Square(2, 0),
#             Square(3, 0),
#             Square(1, 2),
#             Square(2, 2),
#             Square(2, 3),
#         ],
#     )
#     _assert_targets(
#         Action.GRENADES,
#         [
#             Square(2, 3),
#         ],
#     )
