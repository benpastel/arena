

from state import new_state, check_consistency, check_game_result, GameResult
from display import print_state


if __name__ == '__main__':
    # under construction

    state = new_state()
    check_consistency(state)
    assert check_game_result(state) == GameResult.ONGOING

    print_state(state)
