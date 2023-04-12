import asyncio
from typing import Dict, Tuple, Optional, cast, List, Literal

from websockets.server import WebSocketServerProtocol

from arena.server.actions import valid_targets, take_action
from arena.server.state import new_state, State
from arena.server.constants import (
    Player,
    Square,
    GameResult,
    Action,
    Tile,
    OtherAction,
    Response,
    START_POSITIONS,
    other_player,
)
from arena.server.choices import (
    choose_action_or_square,
    choose_square_or_hand,
    choose_response,
    send_prompt,
)
from arena.server.notify import notify_state_changed, notify_selection_changed


def _auto_place_tiles(player: Player, state: State) -> None:
    """Arbitrarily place the starting tiles.  For testing."""
    # TODO consider making this the actual rules and do it when state is initialized
    # also randomize the columns (maybe with rotational symmetry?)
    assert len(START_POSITIONS[player]) == 2

    for target in START_POSITIONS[player]:
        tile = state.tiles_in_hand[player][0]
        state.tiles_in_hand[player].remove(tile)
        state.tiles_on_board[player].append(tile)
        state.positions[player].append(target)


async def _resolve_action(
    start: Square,
    action: Action,
    target: Square,
    state: State,
    websockets: Dict[Player, WebSocketServerProtocol],
) -> None:
    # `hits` is a possibly-empty list of tiles hit by the action
    hits = take_action(start, action, target, state)

    state.log(f"{state.current_player} uses {action}")

    for hit in hits:
        await _lose_tile(hit, state, websockets)


async def _select_action(
    state: State, websockets: Dict[Player, WebSocketServerProtocol]
) -> Tuple[Square, Action, Square]:
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
    websockets: Dict[Player, WebSocketServerProtocol],
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
        player = state.player_at(player_or_square)
        possible_squares = [player_or_square]
    elif player_or_square in Player:
        # they lost a challenge, so they get a choice if they have multiple tiles
        player = player_or_square
        possible_squares = state.positions[player]

    if len(possible_squares) > 1 or len(state.tiles_in_hand[player]) > 0:
        # current player will need to choose something, so set a waiting prompt for opponent
        # and send any state updates so far to both players
        await notify_state_changed(state, websockets)
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
    state.tiles_on_board[player].remove(tile)
    state.positions[player].remove(square)
    state.discard.append(tile)

    # move the replacement tile if applicable
    if replacement:
        state.tiles_in_hand[player].remove(replacement)
        state.tiles_on_board[player].append(replacement)
        state.positions[player].append(square)

    state.log(f"{player} lost {tile}.")
    await notify_state_changed(state, websockets)


async def _select_response(
    start: Square,
    action: Action,
    target: Square,
    state: State,
    websockets: Dict[Player, WebSocketServerProtocol],
) -> Response | Literal[Tile.HOOK]:
    assert action in Tile

    possible_responses: List[Response | Literal[Tile.HOOK]] = [
        Response.ACCEPT,
        Response.CHALLENGE,
    ]
    if action == Tile.HOOK:
        # Tile.HOOK blocks Tile.HOOK
        possible_responses.append(Tile.HOOK)

    await send_prompt(
        "Waiting for opponent to respond.", websockets[state.current_player]
    )

    return await choose_response(
        possible_responses,
        f"Opponent claimed {action}.  Choose your response.",
        websockets[state.other_player],
    )


async def _select_block_response(
    state: State, websockets: Dict[Player, WebSocketServerProtocol]
) -> Response:
    await send_prompt(
        "Waiting for opponent to respond to block.", websockets[state.other_player]
    )
    response = await choose_response(
        [Response.ACCEPT, Response.CHALLENGE],
        f"Opponent blocked with {Tile.HOOK}.  Choose your response.",
        websockets[state.current_player],
    )
    return cast(Response, response)


async def _play_one_turn(
    state: State, websockets: Dict[Player, WebSocketServerProtocol]
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

    # show both players the proposed action
    async with asyncio.TaskGroup() as tg:
        for websocket in websockets.values():
            coroutine = notify_selection_changed(
                state.current_player, start, action, target, websocket
            )
            tg.create_task(coroutine)

    # ask opponent to accept, challenge, or block as appropriate
    response = await _select_response(start, action, target, state, websockets)

    if response == Response.ACCEPT:
        # other player allows the action to proceed
        await _resolve_action(start, action, target, state, websockets)

    elif response == Response.CHALLENGE:
        start_tile = state.tile_at(start)
        msg = f"{state.current_player} reveals a {start_tile}."
        if action == start_tile:
            # challenge fails
            # original action succeeds
            state.log(msg + " Challenge fails!")
            await _lose_tile(state.other_player, state, websockets)
            await _resolve_action(start, action, target, state, websockets)
        else:
            # challenge succeeds
            # original action fails
            state.log(msg + " Challenge succeeds!")
            await _lose_tile(state.current_player, state, websockets)
    else:
        assert response == Tile.HOOK
        # the response was to block a HOOK with a HOOK
        # which the original player may challenge
        block_response = await _select_block_response(state, websockets)
        target_tile = state.tile_at(target)
        reveal_msg = f"{state.other_player} reveals a {target_tile}."

        if block_response == Response.ACCEPT:
            # block succeeds
            # original action fails
            state.log("Hook blocked.")
        elif target_tile == Tile.HOOK:
            # challenge fails
            # block succeeds
            # original action fails
            state.log(reveal_msg + " Challenge fails!")
            await _lose_tile(state.current_player, state, websockets)
        else:
            # challenge succeeds
            # block fails
            # original action succeeds
            state.log(reveal_msg + " Challenge succeeds!")
            await _lose_tile(state.other_player, state, websockets)
            await _resolve_action(start, action, target, state, websockets)


async def play_one_game(
    websockets: Dict[Player, WebSocketServerProtocol]
) -> GameResult:
    """
    Play one game on the connected websockets.

    No graceful handling of disconnects or other websocket exceptions yet.
    """
    print("New game")

    # initialize a new game
    # start with a hardcoded board for now
    # later random + place_tiles
    state = new_state()
    _auto_place_tiles(Player.N, state)
    _auto_place_tiles(Player.S, state)
    state.log("New game!")
    print("Sending initial state to both players.")
    await notify_state_changed(state, websockets)

    while state.game_result() == GameResult.ONGOING:
        state.check_consistency()

        await _play_one_turn(state, websockets)

        state.next_turn()

        await notify_state_changed(state, websockets)

    # later: prompt for a new game with starting player rotated
    # also keep a running total score for longer matches
    state.log(f"Game over!  {state.game_result()}!")
    print(f"Game over!  {state.game_result()}!")
    return state.game_result()
