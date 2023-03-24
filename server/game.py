from enum import Enum
from typing import Tuple

from arena.server.state import (
    new_state,
    GameResult,
    Player,
    Tile,
    Square,
    GameState,
    Action,
    OtherAction,
)
from arena.server.actions import (
    valid_targets,
    take_action,
)
from arena.server.terminal_ui import (
    display_state,
    place_tiles,
    choose_option,
    choose_option_or_cancel,
)


class Response(Enum):
    """
    A response by the other player to a proposed action.  Only some responses are valid
    on any given move.

    They choices are to accept, challenge, or block
    but when blocking, the player must choose a blocking tile.

    We flatten the choice of blocking tile into a single enum to simplify
    the player input.

    Only some options are valid on any given move.
    """

    # accept the action as given
    ACCEPT = "ACCEPT"

    # challenge the action
    CHALLENGE = "CHALLENGE"

    # block a grappling hook by claiming to have a grappling hook
    BLOCK = f"BLOCK AS {Tile.HOOK}"

    def __repr__(self) -> str:
        return self.value


def _select_action(state: GameState) -> Tuple[Square, Action, Square]:
    """
    Prompt the player to choose the action for their turn.

    Returns:
        - square of the tile that's taking the action
        - the action
        - target square of the action
    """
    player_view = state.player_view(state.current_player)

    # choose in a loop
    # to enable canceling our choice and trying again indefinitely
    while True:
        # choose the start square
        possible_starts = state.positions[state.current_player]

        assert 1 <= len(possible_starts) <= 2
        if len(possible_starts) == 1:
            # only one choice
            start = possible_starts[0]
        else:
            start = choose_option(
                possible_starts,
                player_view,
                "Choose the tile that will take an action this turn.",
            )

        # choose the action, or cancel
        actions_and_targets = valid_targets(start, state)
        action = choose_option_or_cancel(
            list(actions_and_targets.keys()),
            player_view,
            f"Choose the action for {state.tile_at(start).value}.",
        )
        if not action:
            # they canceled
            # try again from the start
            continue

        # choose the target square for the action, or cancel
        target = choose_option_or_cancel(
            actions_and_targets[action],
            player_view,
            f"Choose the target square for {action.name}.",
        )
        if not target:
            # they canceled
            # try again for the start
            continue

        # they've chosen everything without canceling
        return start, action, target


def _select_response(
    start: Square,
    action: Action,
    target: Square,
    state: GameState,
) -> Response:
    if action not in Tile:
        # the action doesn't require a response
        # (i.e. moving or smiting)
        return Response.ACCEPT

    msg = f"{start} claims to be {action} and "
    match action:
        case Tile.FLOWER | Tile.BIRD:
            msg += f"wants to move to {target}."
        case Tile.HOOK:
            msg += f"wants to hook {target}."
        case Tile.GRENADES:
            msg += f"wants to throw a grenade at {target}."
        case Tile.KNIVES:
            msg += f"wants to stab {target}."
        case _:
            assert False
    state.log(msg)

    options = [Response.ACCEPT, Response.CHALLENGE]
    if action == Tile.HOOK:
        options.append(Response.BLOCK)

    response = choose_option(
        options,
        state.player_view(state.other_player),
        "Choose your response.",
    )
    return response


def _select_block_response(target: Square, state: GameState) -> Response:
    state.log(f"{target} claims to be {Tile.HOOK} and wants to block.")

    response = choose_option(
        [Response.ACCEPT, Response.CHALLENGE],
        state.player_view(state.current_player),
        "Choose your response.",
    )
    return response


def _lose_tile(player_or_square: Player | Square, state: GameState) -> None:
    """
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
    """

    # inside a loop to enable canceling and retrying
    while True:
        # select which tile on board is lost
        # in some cases the player gets a choice
        if isinstance(player_or_square, Square):
            square = player_or_square
            player = state.player_at(square)
        elif player_or_square in Player and len(state.positions[player_or_square]) == 1:
            # the player only has one tile on board, so they get no choice
            player = player_or_square
            square = state.positions[player][0]
        else:
            # the player gets to choose which to lose
            player = player_or_square
            square = choose_option(
                state.positions[player],
                state.player_view(player),
                "Choose which tile to lose.",
            )

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
            replacement = choose_option_or_cancel(
                state.tiles_in_hand[player],
                state.player_view(player),
                f"Choose which tile to replace {tile.value}.",
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
    state.discard.append(tile)

    # move the replacement tile if applicable
    if replacement:
        state.tiles_in_hand[player].remove(replacement)
        state.tiles_on_board[player].append(replacement)
        state.positions[player].append(square)


def _resolve_action(
    start: Square, action: Action, target: Square, state: GameState
) -> None:
    # `hits` is a possibly-empty list of tiles hit by the action
    hits = take_action(start, action, target, state)

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
            state.log(f"{start} stabs {target}")
        case _:
            assert False

    for hit in hits:
        _lose_tile(hit, state)


def play_one_game():
    # TODO: handle fountain & book tiles

    state = new_state()

    place_tiles(Player.N, state)
    place_tiles(Player.S, state)

    while state.game_result() == GameResult.ONGOING:
        state.check_consistency()

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
        # ask whether they accept, challenge, or block as appropriate
        response = _select_response(start, action, target, state)

        if response == Response.ACCEPT:
            # other player allows the action to proceed
            _resolve_action(start, action, target, state)

        elif response == Response.CHALLENGE:
            start_tile = state.tile_at(start)
            if action == start_tile:
                # challenge fails
                # original action succeeds
                state.log(f"Challenge failed because {start} is a {start_tile}.")
                _lose_tile(state.other_player, state)
                _resolve_action(start, action, target, state)
            else:
                # challenge succeeds
                # original action fails
                state.log(f"Challenge succeeded because {start} is a {start_tile}.")
                _lose_tile(state.current_player, state)
        else:
            # the response was to block
            # blocking means the target is Tile.HOOK in response to a HOOK
            # which the original player may challenge
            block_response = _select_block_response(target, state)
            target_tile = state.tile_at(target)

            if block_response == Response.ACCEPT:
                # block succeeds
                # original action fails
                state.log("Hook blocked.")
            elif target_tile == Tile.HOOK:
                # challenge fails
                # block succeeds
                # original action fails
                state.log(f"Challenge failed because {target} is a {Tile.HOOK}.")
                _lose_tile(state.current_player, state)
            else:
                # challenge succeeds
                # block fails
                # original action succeeds
                state.log(f"Challenge succeeded because {target} is a {target_tile}.")
                _lose_tile(state.other_player, state)
                _resolve_action(start, action, target, state)

        state.turn_count += 1

    display_state(state.json())
    state.log(f"Game over!  {state.game_result()}!")
    # later: prompt for a new game with starting player rotated
    # also keep a running total score for longer matches


if __name__ == "__main__":
    play_one_game()
