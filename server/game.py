import asyncio
import json
from enum import Enum
from typing import List, Dict, Any

import websockets
from websockets.server import WebSocketServerProtocol

from arena.server.state import new_state, Player
from arena.server.actions import valid_targets
from arena.server.terminal_ui import auto_place_tiles
from arena.server.state import Action, OtherAction, Tile, Square


async def _select_action(state: GameState, websocket: WebSocketServerProtocol) -> Tuple[Square, Action, Square]:
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
    while True
        # choose the start square
        possible_starts = state.positions[state.current_player]

        assert 1 <= len(possible_starts) <= 2
        if len(possible_starts) == 1:
            # only one choice
            start = possible_starts[0]
        else:
            start = await choose_start(
                possible_starts,
                websocket
            )

        # choose the action, or cancel by choosing the other start square
        actions_and_targets = valid_targets(start, state)

        # TODO: LEFT OFF HERE

        # they've chosen everything without canceling
        return start, action, target


async def _play_one_turn(
    state: GameState,
    websockets: websockets: Dict[Player, WebSocketServerProtocol]
) -> None:
    """
    Play one turn, prompting both players as needed.

    Updates `state` with the result of the turn, but doesn't transition to the next turn
    or display that state to the players.

    TODO:
        - when to set prompt  on the other player to "waiting for opponent to X"?
    """
    # current player chooses their move
    start, action, target = await _select_action(state, websockets[state.current_player])

    if not action in Tile:
        assert action in OtherAction
        # the player didn't claim a tile
        # i.e. they moved or smited
        # so no possibility of challenge
        await _resolve_action(start, action, target, state, websockets)
        return

    # show other player the proposed action
    # ask whether they accept, challenge, or block as appropriate
    response = await _select_response(start, action, target, state, websockets[state.other_player])

    if response == Response.ACCEPT:
        # other player allows the action to proceed
        await _resolve_action(start, action, target, state, websockets)

    elif response == Response.CHALLENGE:
        start_tile = state.tile_at(start)
        if action == start_tile:
            # challenge fails
            # original action succeeds
            state.log(f"Challenge failed because {start} is a {start_tile}.")
            await _lose_tile(state.other_player, state, websockets[state.other_player])
            await _resolve_action(start, action, target, state, websockets)
        else:
            # challenge succeeds
            # original action fails
            state.log(f"Challenge succeeded because {start} is a {start_tile}.")
            await _lose_tile(state.current_player, state, websockets[state.current_player])
    else:
        # the response was to block
        # blocking means the target is Tile.HOOK in response to a HOOK
        # which the original player may challenge
        block_response = await _select_block_response(target, state, websockets[state.current_player])
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
            await _lose_tile(state.current_player, state, websockets[state.current_player])
        else:
            # challenge succeeds
            # block fails
            # original action succeeds
            state.log(f"Challenge succeeded because {target} is a {target_tile}.")
            await _lose_tile(state.other_player, state, websockets[state.other_player])
            await _resolve_action(start, action, target, state, websockets)


async def play_one_game(
    websockets: websockets: Dict[Player, WebSocketServerProtocol]
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
    auto_place_tiles(Player.N, state)
    auto_place_tiles(Player.S, state)
    state.log("log line 1")
    state.log("log line 2")
    print("Sending initial state to both players.")

    while state.game_result() == GameResult.ONGOING:
        state.check_consistency()

        # send the state to each player
        # TODO: later:
        #  - also pass valid_actions for highlighting
        #  - also dispaly turn count
        async with asyncio.TaskGroup() as tg:
            for player in Player:
                player_view = game_state.player_view(player)
                state_event = {
                    "type": OutEventType.GAME_STATE_CHANGE.value,
                    "playerView": player_view.dict(),
                }
                message = json.dumps(state_event)
                tg.create_task(websocket.send(message))

        _play_one_turn(state, websockets)
        state.next_turn()

    # later: prompt for a new game with starting player rotated
    # also keep a running total score for longer matches
    state.log(f"Game over!  {state.game_result()}!")
    print(f"Game over!  {state.game_result()}!")
    return state.game_result()