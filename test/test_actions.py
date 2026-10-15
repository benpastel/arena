from itertools import combinations

from server.state import Square
from server.constants import ROWS, COLUMNS
from server.actions import _all_distances, _fireball_targets, path


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


def test_path():
    # straight and diagonal lines
    assert path(Square(0, 0), Square(0, 2)) == [Square(0, 1), Square(0, 2)]
    assert path(Square(2, 2), Square(0, 0)) == [Square(1, 1), Square(0, 0)]
    assert path(Square(1, 1), Square(1, 1)) == []

    # off the lines (a knight move, or two steps round a corner): diagonal, then straight
    assert path(Square(0, 0), Square(1, 2)) == [Square(1, 1), Square(1, 2)]
    assert path(Square(4, 4), Square(2, 3)) == [Square(3, 3), Square(2, 3)]


def test_a_move_always_exists():
    # a player out of time makes a random ↕ move (game._random_move), so one of their
    # tiles must always have an empty square next to it, however the board's tiles
    # (at most 2 each) are placed
    squares = [Square(r, c) for r in range(ROWS) for c in range(COLUMNS)]
    for count in range(2, 5):
        for placed in combinations(squares, count):
            for own_count in range(1, min(count, 3)):
                if count - own_count > 2:
                    continue
                for own in combinations(placed, own_count):
                    assert any(
                        any(
                            dist == 1 and s not in placed
                            for s, dist in _all_distances(
                                start, [p for p in placed if p != start]
                            ).items()
                        )
                        for start in own
                    ), placed
