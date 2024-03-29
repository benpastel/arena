from typing import Optional, cast, Literal
from random import shuffle

from websockets.server import WebSocketServerProtocol

from server.actions import (
    valid_targets,
    take_action,
    reflect_action,
    grapple_end_square,
)
from server.state import new_state, State
from server.constants import (
    Player,
    Square,
    GameResult,
    Action,
    Tile,
    OtherAction,
    Response,
    other_player,
)
from server.choices import (
    choose_action_or_square,
    choose_square_or_hand,
    choose_response,
    choose_exchange,
    send_prompt,
)
from server.notify import (
    broadcast_state_changed,
    notify_selection_changed,
    broadcast_selection_changed,
    clear_selection,
)


async def _resolve_bonus(
    square: Square,
    state: State,
) -> None:
    """Give a player bonus $ for moving onto the bonus square"""
    player = state.player_at(square)
    state.log(f"{player.format_for_log()}: +${state.bonus_amount} bonus")
    state.coins[player] += state.bonus_amount


async def _move_x2(
    square: Square,
    state: State,
    websockets: dict[Player, WebSocketServerProtocol],
) -> None:
    """Allow the player to move the x2 highlight."""
    player = state.player_at(square)
    await send_prompt(
        "Waiting for opponent to move the ×2.",
        websockets[other_player(player)],
    )
    choices: list[Action] = [t for t in Tile if t != state.x2_tile and t != Tile.HIDDEN]
    choice = await choose_action_or_square(
        choices,
        [],
        "Move the ×2 to a different action.",
        websockets[player],
    )
    assert isinstance(choice, Tile)
    state.x2_tile = choice
    state.log(f"{player.format_for_log()} moved ×2 to {choice}")

    await broadcast_state_changed(state, websockets)


async def _resolve_exchange(
    square: Square,
    state: State,
    websockets: dict[Player, WebSocketServerProtocol],
) -> None:
    """Allow a player to exchange with a exchange square"""
    player = state.player_at(square)
    exchange_index = state.exchange_positions.index(square)
    tile_on_board_index = state.positions[player].index(square)

    # player can now see the exchange position
    state.exchange_tiles_revealed[player][exchange_index] = True

    await broadcast_state_changed(state, websockets)
    await send_prompt(
        "Waiting for opponent to exchange tiles.",
        websockets[other_player(player)],
    )

    # if they could, other player can no longer see the exchange position or tile
    # because it may have change
    state.exchange_tiles_revealed[other_player(player)][exchange_index] = False
    state.tiles_on_board_revealed[player][tile_on_board_index] = False

    old_tile = state.tile_at(square)
    exchange_choices = state.exchange_tiles[exchange_index] + [old_tile]
    choice = await choose_exchange(
        exchange_choices,
        "Exchange tiles, or keep your current tile.",
        websockets[player],
    )

    if choice != old_tile:
        # they swapped with a exchange tile
        state.tiles_on_board[player][tile_on_board_index] = choice
        state.exchange_tiles[exchange_index].remove(choice)
        state.exchange_tiles[exchange_index].append(old_tile)

        # shuffle to hide which tile they placed
        shuffle(state.exchange_tiles[exchange_index])

    state.log(f"{player.format_for_log()} may have exchanged tiles.")


async def _resolve_action(
    start: Square,
    action: Action,
    target: Square,
    state: State,
    websockets: dict[Player, WebSocketServerProtocol],
    reflect: bool = False,
) -> None:
    if state.x2_tile == action:
        repeats = 2
        x2_msg = "2X "
    else:
        repeats = 1
        x2_msg = ""

    # `hits` is a possibly-empty list of tiles hit by the action
    if reflect:
        hits = reflect_action(start, action, target, state)
        state.log(f"{state.other_player.format_for_log()} reflects {x2_msg}{action}")
    else:
        hits = take_action(start, action, target, state)
        state.log(f"{state.current_player.format_for_log()} uses {x2_msg}{action}")

    for repeat in range(repeats):
        if repeats > 1 and hits:
            state.log(f"{repeat + 1} / {repeats} - ")

        for hit in hits:
            await _lose_tile(hit, state, websockets)

        await clear_selection(websockets)

    # we may have moved onto a special square
    if action in (OtherAction.MOVE, Tile.FLOWER, Tile.BIRD):
        if target == state.bonus_position:
            await _move_x2(target, state, websockets)

        if target in state.exchange_positions:
            await _resolve_exchange(target, state, websockets)

    # hook may have moved someone onto one
    if action == Tile.HOOK:
        if reflect:
            end_square = grapple_end_square(target, start, obstructions=[])
        else:
            end_square = grapple_end_square(start, target, obstructions=[])

        if end_square == state.bonus_position:
            await _move_x2(end_square, state, websockets)

        if end_square in state.exchange_positions:
            await _resolve_exchange(end_square, state, websockets)


async def _select_action(
    state: State, websockets: dict[Player, WebSocketServerProtocol]
) -> tuple[Square, Action, Square]:
    """
    Prompt the player to choose the action for their turn.

    Returns:
        - square of the tile that's taking the action
        - the action
        - target square of the action
    """
    await send_prompt(
        "Waiting for opponent to select their action.", websockets[state.other_player]
    )
    websocket = websockets[state.current_player]

    possible_starts = state.positions[state.current_player]
    assert 1 <= len(possible_starts) <= 2
    if len(possible_starts) == 1:
        # only one choice
        start = possible_starts[0]
    else:
        choice = await choose_action_or_square(
            [], possible_starts, "Select a tile.", websocket
        )
        start = cast(Square, choice)

    # choose in a loop
    # to allow changing out choice of start square & action
    action: Optional[Action] = None
    while True:
        actions_and_targets = valid_targets(start, state)
        possible_actions = list(actions_and_targets.keys())
        possible_targets = actions_and_targets.get(cast(Action, action), [])

        # display the partial selection and valid actions/targets to the
        # current player
        await notify_selection_changed(
            state.current_player, start, action, None, websocket
        )

        if not action and len(possible_starts) == 1:
            possible_squares = []
            prompt = "Select an action."
        elif not action:
            possible_squares = possible_starts
            prompt = "Select an action, or a different tile."
        elif len(possible_starts) == 1:
            possible_squares = possible_targets
            prompt = "Select a target, or a different action."
        else:
            possible_squares = possible_starts + possible_targets
            prompt = "Select a target, or a different action or tile."

        choice = await choose_action_or_square(
            possible_actions, possible_squares, prompt, websocket
        )
        if choice in possible_targets:
            # they chose a target
            # we should now have all 3 selected
            assert action is not None
            target = cast(Square, choice)

            # show both players the proposed action
            await broadcast_selection_changed(
                state.current_player, start, action, target, websockets
            )
            return start, action, target
        elif choice in possible_actions:
            # they chose an action
            # go around again for the target or different action
            action = cast(Action, choice)
        else:
            # they chose a start square
            # go around again for the action or different start
            assert choice in possible_starts
            start = cast(Square, choice)
            action = None


async def _lose_tile(
    player_or_square: Player | Square,
    state: State,
    websockets: dict[Player, WebSocketServerProtocol],
) -> None:
    """
     - Prompt the player to choose a tile to lose, if applicable
     - choose the tile to replace it, if applicable
     - log the lost tile
     - update state

    If `player_or_square` is a square, the player must lose the tile on that square.
    (E.g. when that tile was hit by an attack.)

    If `player_or_square` is a player, the player chooses one tile on board to lose.
    (E.g. when the player lost a challenge.)
    We allow the player to cancel and retry that choice when they get to the replacement
    tile.
    """

    # select which tile on board is lost
    # in some cases the player gets a choice
    if isinstance(player_or_square, Square):
        # a specific square was lost to an attack, so they get no choice
        try:
            player = state.player_at(player_or_square)
        except ValueError:
            # if a double-attack killed the square and nothing replaced it,
            # it's possible the square is empty
            # in which case nothing happens
            return
        possible_squares = [player_or_square]
    else:
        # they lost a challenge, so they get a choice if they have multiple tiles
        assert player_or_square in Player
        player = player_or_square
        possible_squares = state.positions[player]

    if len(possible_squares) == 0:
        # they have no tiles to lose
        # i.e. their last tile was already killed by action
        return

    if len(possible_squares) > 1 or len(state.tiles_in_hand[player]) > 0:
        # current player will need to choose something, so set a waiting prompt for opponent
        # and send any state updates so far to both players
        await broadcast_state_changed(state, websockets)
        await send_prompt(
            "Waiting for opponent to lose tile.", websockets[other_player(player)]
        )

    websocket = websockets[player]
    if len(possible_squares) > 1:
        choice = await choose_square_or_hand(
            possible_squares,
            [],
            "Choose which tile to lose.",
            websocket,
        )
        square = cast(Square, choice)
    else:
        square = possible_squares[0]

    # choose replacement tile from hand in a loop
    # to enable choosing a different square to lose
    while True:
        # mark the selected tile with an X for this player
        await notify_selection_changed(
            player, start=None, action=None, target=square, websocket=websocket
        )

        tile = state.tile_at(square)
        hand_tiles = state.tiles_in_hand[player]

        if len(hand_tiles) == 0:
            # the player has no tiles in hand, so no choice
            replacement = None
            break

        if len(hand_tiles) == 1:
            # the player only has one tile in hand, so no choice
            replacement = hand_tiles[0]
            break

        if len(possible_squares) == 1:
            # the player chooses the replacement tile
            choice = await choose_square_or_hand(
                possible_squares=[],
                possible_hand_tiles=hand_tiles,
                prompt="Choose the replacement tile from your hand.",
                websocket=websocket,
            )
            replacement = cast(Tile, choice)
            break

        # otherwise, the player chooses the replacement tile or changes the lost tile
        choice = await choose_square_or_hand(
            possible_squares=possible_squares,
            possible_hand_tiles=hand_tiles,
            prompt="Choose the replacement tile from your hand, or a different tile to lose.",
            websocket=websocket,
        )
        if choice in hand_tiles:
            replacement = cast(Tile, choice)
            break
        else:
            # they changed the lost tile
            # go around the loop again to choose the replacement
            assert choice in possible_squares
            square = cast(Square, choice)
            continue

    # move the tile from alive to dead
    position_index = state.positions[player].index(square)
    state.tiles_on_board[player].pop(position_index)
    state.positions[player].pop(position_index)
    state.tiles_on_board_revealed[player].pop(position_index)
    state.discard.append(tile)

    # move the replacement tile if applicable
    if replacement:
        state.tiles_in_hand[player].remove(replacement)
        state.tiles_on_board[player].append(replacement)
        state.positions[player].append(square)
        state.tiles_on_board_revealed[player].append(False)
        state.log(
            f"{player.format_for_log()} lost {tile} on {square.format_for_log()} and replaced it from hand."
        )
    else:
        state.log(
            f"{player.format_for_log()} lost {tile} on {square.format_for_log()}."
        )

    state.score_point(other_player(player))
    await clear_selection(websockets)
    await broadcast_state_changed(state, websockets)


async def _select_response(
    start: Square,
    action: Action,
    target: Square,
    state: State,
    websockets: dict[Player, WebSocketServerProtocol],
) -> Response | Literal[Tile.HOOK, Tile.KNIVES]:
    assert action in Tile

    possible_responses: list[Response | Literal[Tile.HOOK, Tile.KNIVES]] = [
        Response.ACCEPT,
        Response.CHALLENGE,
    ]
    if action == Tile.HOOK:
        # Tile.HOOK reflects Tile.HOOK
        possible_responses.append(Tile.HOOK)
    elif action == Tile.KNIVES:
        # Tile.KNIVES reflects Tile.KNIVES
        possible_responses.append(Tile.KNIVES)

    await send_prompt(
        "Waiting for opponent to respond.", websockets[state.current_player]
    )

    return await choose_response(
        possible_responses,
        f"Opponent claimed {action}.  Choose your response.",
        websockets[state.other_player],
    )


async def _select_reflect_response(
    action: Action, state: State, websockets: dict[Player, WebSocketServerProtocol]
) -> Response:
    await send_prompt(
        "Waiting for opponent to respond to reflect.", websockets[state.other_player]
    )
    response = await choose_response(
        [Response.ACCEPT, Response.CHALLENGE],
        f"Opponent reflected with {action}.  Choose your response.",
        websockets[state.current_player],
    )
    return cast(Response, response)


async def _play_one_turn(
    state: State, websockets: dict[Player, WebSocketServerProtocol]
) -> None:
    """
    Play one turn, prompting both players for choices as needed.

    Updates `state` with the result of the turn. Doesn't transition to the next turn
    or display that state to the players.
    """
    # current player chooses their move
    start, action, target = await _select_action(state, websockets)
    if not action in Tile:
        assert action in OtherAction
        # the player didn't claim a tile
        # i.e. they moved or smited
        # so no possibility of challenge
        await _resolve_action(start, action, target, state, websockets)
        return

    # ask opponent to accept, challenge, or reflect as appropriate
    response = await _select_response(start, action, target, state, websockets)

    if response == Response.ACCEPT:
        # other player allows the action to proceed
        await _resolve_action(start, action, target, state, websockets)

    elif response == Response.CHALLENGE:
        state.reveal_at(start)
        start_tile = state.tile_at(start)
        msg = f"{state.current_player.format_for_log()} reveals a {start_tile}."
        if action == start_tile:
            # challenge fails
            # original action succeeds
            state.log(
                msg
                + f" Challenge fails!  First the {action} happens, then {state.other_player.format_for_log()} will choose a tile to lose."
            )
            await _resolve_action(start, action, target, state, websockets)
            await _lose_tile(state.other_player, state, websockets)
        else:
            # challenge succeeds
            # original action fails
            state.log(msg + " Challenge succeeds!")
            await clear_selection(websockets)
            await _lose_tile(state.current_player, state, websockets)
    else:
        assert response in (Tile.HOOK, Tile.KNIVES)
        assert action == response
        # the response was to reflect hook with hook or knives with knives
        # which the original player may challenge
        reflect_response = await _select_reflect_response(response, state, websockets)
        target_tile = state.tile_at(target)
        reveal_msg = f"{state.other_player.format_for_log()} reveals a {target_tile}."

        if reflect_response == Response.ACCEPT:
            # reflect succeeds
            # original action fails
            state.log("Hook reflected.")
            await clear_selection(websockets)
            await _resolve_action(
                start, action, target, state, websockets, reflect=True
            )
        elif target_tile == response:
            # challenge fails
            # reflect succeeds
            # original action fails
            state.reveal_at(target)
            state.log(
                reveal_msg
                + f" Challenge fails!  First the {response} is reflected, then {state.current_player.format_for_log()} will choose a tile to lose."
            )
            await clear_selection(websockets)
            await _resolve_action(
                start, action, target, state, websockets, reflect=True
            )
            await _lose_tile(state.current_player, state, websockets)
        else:
            state.reveal_at(target)
            # challenge succeeds
            # reflect fails
            # original action succeeds
            state.log(
                reveal_msg
                + f" Challenge succeeds!  First the {action} happens, then {state.other_player.format_for_log()} will choose a tile to lose."
            )
            await _resolve_action(start, action, target, state, websockets)
            await _lose_tile(state.other_player, state, websockets)


async def play_one_game(
    match_score: dict[Player, int], websockets: dict[Player, WebSocketServerProtocol]
) -> dict[Player, int]:
    """
    Play one game on the connected websockets.

    Returns the game score.

    No graceful handling of disconnects or other websocket exceptions yet.
    """
    # initialize a new game
    state = new_state(match_score)
    state.log("New game!")
    print("Sending initial state to both players.")
    await broadcast_state_changed(state, websockets)

    while state.game_result() == GameResult.ONGOING:
        state.check_consistency()

        await _play_one_turn(state, websockets)

        state.next_turn()

        await broadcast_state_changed(state, websockets)

    state.log(f"Game over!  {state.game_result()}!")
    await broadcast_state_changed(state, websockets)
    return state.game_score
