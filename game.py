from arena.state import (
    new_state,
    check_consistency,
    check_game_result,
    GameResult,
    Player,
    player_view,
)
from arena.display import print_state


if __name__ == "__main__":
    # under construction

    state = new_state()
    check_consistency(state)
    assert check_game_result(state) == GameResult.ONGOING

    print("Private server state:")
    print_state(state)

    print("\n\n\nNorth's view:")
    print_state(player_view(state, Player.N))

    print("\n\n\nSouth's view:")
    print_state(player_view(state, Player.S))
