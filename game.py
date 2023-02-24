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


def _lose_tile(player_or_square: Player | Square, state: State) -> None:
    '''
     - Prompt the player to choose a tile to lose
     - choose the tile to replace it
     - log the lost tile
     - update state

    If `player_or_square` is a square, the player must lose the tile on that square.
    (E.g. when that tile was hit by an attack.)

    If `player_or_square` is a player, the player chooses one tile on board to lose.
    (E.g. when the player lost a challenge.)
    We allow the player to cancel and retry that choice when they get to the replacement
    tile.
    '''

    # inside a loop to enable canceling and retrying
    while True:

        # select which tile on board is lost
        # in some cases the player gets a choice
        if isinstance(player_or_square, Square):
            square = player_or_square
            player = state.player_at(square)
            allow_cancel_later = False
        elif player_or_square in Player and len(state.positions[player]) == 1:
            # the player only has one tile on board, so they get no choice
            player = player_or_square
            square = state.positions[player][0]
            allow_cancel_later = False
        else:
            # the player gets to choose which to lose
            player = player_or_square
            square = choose_square(
                state.positions[player],
                state.player_view(player),
                "Choose which tile to lose.",
                allow_cancel = False
            )
            allow_cancel_later = True

        tile = state.tile_at(square)

        # select which tile from hand replaces it, if applicable
        if len(state.tiles_in_hand[player]) == 0:
            # the player has no tiles in hand
            replacement = None

        elif len(state.tiles_in_hand[player]) == 1:
            # the player only has one tile in hand, so no choice
            replacement = state.tiles_in_hand[player][0]

        else:
            # the player gets to choose the replacement tile
            replacement = choose_tile(
                state.tiles_in_hand[player],
                state.player_view(player),
                f"Choose which tile to replace {tile.value}.",
                allow_cancel = True
            )
            if replacement is None:
                # they canceled
                # try again from the start
                continue

        # we've successfully chosen a square to lose & replacement tile if applicable
        break

    state.log(f"{player} lost {tile} at {square}.")

    # move the tile from alive to dead
    state.tiles_on_board[player].remove(tile)
    state.positions[player].remove(square)
    discard.append(tile)

    # move the replacement tile if applicable
    if replacement:
        state.tiles_in_hand[player].remove(replacement)
        state.tiles_on_board[player].append(replacement)
        state.positions[player].append(square)



def _resolve_action(start: Square, action: Action, target: Square, state: State) -> None:

    # `hits` is a possibly-empty list of tiles hit by the action
    hits = take_action(start, action, target, state)

    # log what happened
    match action:
        case OtherAction.MOVE:
            state.log(f"{start} moves to {target}")
        case OtherAction.SMITE:
            state.log(f"{start} smites {target}")
        case Tile.FLOWER | Tile.BIRD:
            state.log(f"{start} uses {action} to move to {target}")
        case Tile.HOOK:
            state.log(f"{start} hooks {target}")
        case Tile.GRENADES:
            state.log(f"{start} throws a grenade at {target}, hitting {hits}")
        case Tile.KNIVES:
            state.log(f"{start} hits {target} with a knife")
        case _:
            assert False

    for hit in hits:
        _lose_tile(hit, state)


def _place_tiles(player: Player, state: State) -> None:
    assert False, "TODO"


def play_one_game():
    state = new_state()

    _place_tiles(player.N, state)
    _place_tiles(player.S, state)

    while check_game_result(state) == GameResult.ONGOING:
        check_consistency(state)

        # current player chooses their move
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
                # LEFT OFF HERE: replacing all the "log" placeholders with actual log messages
                #
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
