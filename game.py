

from state import new_state, check_consistency, check_game_result, GameResult


if __name__ == '__main__':
    # under construction
    #
    # for now, just create a new state and check it's consistent

    state = new_state()
    check_consistency(state)
    assert check_game_result(state) == GameResult.ONGOING
