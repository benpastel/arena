from server.state import Square
from server.actions import _all_distances, _fireball_targets


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
        Square(2, 1): 1,
        Square(0, 1): 1,
        Square(0, 0): 2,
        Square(1, 0): 2,
        Square(3, 1): 2,
        Square(3, 2): 2,
        Square(2, 0): 2,
        Square(3, 0): 3,
    }


def test_fireball_targets():
    # Test board looks like this:
    #
    #   . A A . .
    #   E . X . .
    #   E . . . .
    #   . . . . A
    #   . . . . .
    #
    # - caster X at (1,2)
    # - A for ally
    # - E for enemy
    # so:
    # - the top left explosion is valid because it hits the (1, 0) enemy
    # - the bottom left explosion is valid because it hits the (2, 0) enemy
    # - the other two explosions are invalid because they don't hit any enemies
    start = Square(1, 2)
    enemies = [
        Square(1, 0),
        Square(2, 0),
    ]
    allies = [
        Square(0, 1),
        Square(0, 2),
        Square(3, 4),
    ]
    obstructions = enemies + allies

    targets = _fireball_targets(start, obstructions, enemies)

    assert sorted(targets) == sorted(
        [
            Square(0, 1),
            Square(3, 0),
        ]
    )
