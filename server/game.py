import asyncio
import json
from enum import Enum
from typing import List, Dict, Any

import websockets
from websockets.server import WebSocketServerProtocol

from arena.server.state import new_state, Player
from arena.server.actions import valid_targets, take_action
from arena.server.terminal_ui import auto_place_tiles
from arena.server.state import Action, OtherAction, Tile, Square
from arena.server.choices import choose_action_or_square, choose_square_or_hand



def _resolve_action(
    start: Square,
    action: Action,
    target: Square,
    state: GameState,
    websockets: Dict[Player, WebSocketServerProtocol]
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
        _lose_tile(hit, state, websockets)


async def _select_action(
    state: GameState,
    websocket: WebSocketServerProtocol
) -> Tuple[Square, Action, Square]:
    """
    Prompt the player to choose the action for their turn.

    Returns:
        - square of the tile that's taking the action
        - the action
        - target square of the action
    """
    player_view = state.player_view(state.current_player)

    possible_starts = state.positions[state.current_player]
    assert 1 <= len(possible_starts) <= 2
    if len(possible_starts) == 1:
        # only one choice
        start = possible_starts[0]
    else:
        start = await choose_action_or_square(
            [],
            possible_starts,
            websocket,
            "Select a tile."
        )

    # choose in a loop
    # to allow changing out choice of start square & action
    action: Optional[Action] = None
    while True:
        actions_and_targets = valid_targets(start, state)
        possible_actions = list(actions_and_targets.keys())

        if not action and len(possible_starts) == 1:
            possible_squares = []
            prompt = "Select an action."
        elif not action:
            possible_squares = possible_starts
            prompt = "Select an action, or a different tile."
        elif len(possible_starts) == 1:
            possible_squares = actions_and_targets[action]
            prompt = "Select a target, or a different action."
        else:
            possible_squares = possible_starts + actions_and_targets[action]
            prompt = "Select a target, or a different action or tile."

        choice = await choose_action_or_square(
            possible_actions,
            possible_squares,
            websocket,
            prompt
        )
        if choice in possible_targets:
            # they chose a target
            # we should now have all 3 selected
            assert action is not None
            return start, action, choice
        elif choice in possible_actions:
            # they chose an action
            # go around again for the target or different action
            action = choice
        else:
            # they chose a start square
            # go around again for the action or different start
            assert choice in possible_starts
            action = None

        # TODO: send a notification to the choosing player
        # so we can display their partial choices so far


def _lose_tile(player_or_square: Player | Square, state: GameState, websockets: Dict[Player, WebSocketServerProtocol]) -> None:
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

    websocket = websockets[player]
    if len(possible_starts) > 1:
        square = await choose_square_or_hand(
            possible_squares = possible_squares,
            possible_hand = [],
            websocket=websocket,
            prompt="Choose which tile to lose.",
        )

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
            replacement = await choose_square_or_hand(
                possible_squares = [],
                possible_hand_tiles = hand_tiles,
                websocket=websocket,
                prompt="Choose the replacement tile from your hand.",
            )
            break

        # otherwise, the player chooses the replacement tile or changes the lost tile
        choice = await choose_square_or_hand(
            possible_squares = possible_squares,
            possible_hand_tiles = hand_tiles,
            websocket=websocket,
            prompt="Choose the replacement tile from your hand, or a different tile to lose.",
        )
        if choice in hand_tiles:
            replacement = choice
            break
        else:
            # they changed the lost tile
            # go around the loop again to choose the replacement
            assert choice in possible_squares
            square = choice
            continue

    # we've successfully chosen a square to lose & replacement tile if applicable
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


async def play_one_turn(
    state: GameState,
    websockets: Dict[Player, WebSocketServerProtocol]
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