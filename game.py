from arena.state import (
    new_state,
    check_consistency,
    check_game_result,
    GameResult,
    Player,
    player_view,
    ACTION_TO_TILES,
    RESPONSE_TO_SPELL
)
from arena.actions import (
    affordable_actions,
    valid_targets,
    is_challenge_successful,
    resolve_action
)
from arena.display import (
    display_state,
    display_targets,
    display_proposed_action
)

from arena.inputs import (
    select_action,
    select_target_or_cancel,
    challenge_or_accept
)
from arena.logs import (
    log_proposed_action,
    log_challenge_success,
    log_challenge_failure,
    log_action_result
)


def _select_action(state: State) -> Tuple[Square, Action, Square]:
    '''
    Prompt the player to choose the action for their turn.

    Returns:
        - square of the tile that's taking the action
        - the action
        - target square of the action
    '''
    player = state.current_player()
    player_view = state.player_view(player)

    # choose in a loop
    # to enable canceling our choice and trying again indefinitely
    while True:
        # choose the start square
        possible_starts = state.tiles_on_board[player]

        assert 1 <= len(possible_starts) <= 2
        if len(possible_starts) == 1:
            # only one choice
            start = possible_starts[0]
        else:
            start = choose_square(
                possible_starts,
                player_view,
                "Choose the tile that will take an action this turn.",
                allow_cancel = False
            )
            assert start

        # choose the action, or cancel
        actions_and_targets = valid_targets(start, state)
        action = choose_action(
            actions_and_targets.keys(),
            player_view,
            f"Choose the action for {state.tile_at(start).value}.",
            allow_cancel = True
        )
        if action is None:
            # they canceled
            # try again from the start
            continue

        # choose the target square for the action, or cancel
        target = choose_square(
            actions_and_targets[action],
            player_view,
            f"Choose the target square for {action.name}.",
            allow_cancel = True
        )

        if target is None:
            # they canceled
            # try again for the start
            continue

        # they've chosen everything without canceling
        return start, action, target



def _lose_tile(wizards: List[Wizard], state: State) -> None:
    '''
    Prompt the player to choose a tile to lose, and log the choice

    TODO rewrite
    '''
    assert wizards

    # flatten options
    options = [
        (wizard, tile, tile_idx)
        for wizard in wizards
        for tile_idx, tile in enumerate(wizard_tiles[wizard])
    ]

    if len(options) == 0:
        # these wizards have already lost all their tiles; do nothing
        return

    if len(options) == 1:
        # there's no choice
        wizard, tile, tile_idx = options[0]

    else:
        # ask the player
        wizard, tile, tile_idx = select_tile_to_lose(options)

    # move the tile tile from live to dead
    state.wizard_tiles[wizard].pop(tile_idx)
    dead_tiles[wizard].append(tile)
    log_tile_lost(wizard, tile)

    # if this was the wizard's last tile, the wizard is now KO'd
    if not wizard_tiles[wizard]:
        log_wizard_lost(wizard)


def _resolve_action(action: Action, target: Square | Wizard, state: State) -> None:
    log_action(start, action, target, state)

    # the action may hit any number of
    hit_wizards = take_action(source, action, target)

    for hit_wizard in hit_wizards:
        _lose_tile(hit_wizard, state)


def _redraw_tile(wizard: Wizard, action: Action, state: State) -> None:
    # return the tile in state
    # draw a new tile at random
    # display & log this for the player who can see it
    assert False, "TODO"


def play_one_game():
    state = new_state()

    # TODO
    _place_tiles(player.N, state)
    _place_tiles(player.S, state)

    while check_game_result(state) == GameResult.ONGOING:
        check_consistency(state)

        start, action, target = _select_action(state)

        if not action in Tile:
            assert action in OtherAction
            # the player didn't claim a tile
            # i.e. they moved or smited
            # so no possibility of challenge
            _resolve_action(start, action, target, state)
            state.turn_count += 1
            continue

        # show other player the proposed action
        # ask whether they accept, challenge, or block
        response = _select_response(start, action, target, state)

        if response == Response.ACCEPT:
            # other player allows the action to proceed
            _resolve_action(start, action, target, state)

        elif response == Response.CHALLENGE:
            if action == state.tile_at(start):
                # challenge fails
                # original action succeeds
                log_challenge_failure(action)
                _lose_tile(state.other_player(), state)
                _resolve_action(action, target, state)
            else:
                # challenge succeeds
                # original action fails
                log_challenge_success(start, action)
                _lose_tile(state.current_player(), state)
        else:
            # the response was to block
            # blocking means the target is Tile.HOOK in response to a HOOK
            # which the original player may challenge
            block_response = _select_block_response(target, state)

            if block_response == Response.ACCEPT:
                # block succeeds
                # original action fails
                log_block_success()

            elif state.tile_at(target) == Tile.HOOK:
                # challenge fails
                # block succeeds
                # original action fails
                log_challenge_failure(target, Tile.HOOK)
                _lose_tile(state.current_player(), state)
            else:
                # challenge succeeds
                # block fails
                # original action succeeds
                log_challenge_success(target, Tile.HOOK)
                _lose_tile(state.other_player(), state)
                _resolve_action(start, action, target, state)

        state.turn_count += 1

    display_state(state)
    log_game_end()

    # later: prompt for a new game with starting player rotated
    # also keep a running total score for longer matches


def show_start_views():
    ''' Start a new game and show both players' views, for debugging. '''
    state = new_state()
    check_consistency(state)
    assert check_game_result(state) == GameResult.ONGOING

    print("Private server state:")
    display_state(state)

    print("\n\n\nNorth's view:")
    display_state(player_view(state, Player.N))

    print("\n\n\nSouth's view:")
    display_state(player_view(state, Player.S))


if __name__ == "__main__":
    play_one_game()
