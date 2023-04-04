#!/usr/bin/env python3

import asyncio
import json
from enum import Enum
from typing import List, Dict, Any

import websockets
from websockets.server import WebSocketServerProtocol

from arena.server.state import new_state, Player
from arena.server.actions import valid_targets
from arena.server.terminal_ui import auto_place_tiles

# from arena.server.game import _resolve_action
from arena.server.state import Action, OtherAction, Tile, Square

from arena.server.action_chooser import ActionChooser


def _parse_action(action_string: str) -> Action:
    try:
        return OtherAction(action_string)
    except:
        pass

    try:
        return Tile(action_string)  # type: ignore
    except:
        pass

    raise ValueError(f"Unknown {action_string=}")


class InEventType(str, Enum):
    # values must match the JS event type strings
    CHOOSE_START = "CHOOSE_START"
    CHOOSE_ACTION = "CHOOSE_ACTION"
    CHOOSE_TARGET = "CHOOSE_TARGET"


class OutEventType(str, Enum):
    # values must match the JS event type strings

    # change in the persistent game state (tiles on board, tiles in hand, mana, etc)
    GAME_STATE_CHANGE = "GAME_STATE_CHANGE"

    # change in the player's selection (start, action, target)
    TURN_STATE_CHANGE = "TURN_STATE_CHANGE"



# # currently valid actions => targets
# # based on both the game state and the actionChooser state
# action_targets: Dict[Action, List[Square]] = {}

# async for message in websocket:
#     # TODO
#     #    - check it is from the correct player
#     #    - check it is valid
#     #    - if so, make move on board & send "board updated!" message to player
#     #   worry about challenges & responses later
#     event = json.loads(message)
#     print(f"Received {event=}")
#     in_event_type = InEventType(event["type"])

#     if in_event_type == InEventType.CHOOSE_START:
#         start = Square.from_list(event["start"])
#         changed = actionChooser.tryChooseStart(
#             start, state.positions[state.current_player]
#         )
#         if changed:
#             action_targets = valid_targets(start, state)

#     elif in_event_type == InEventType.CHOOSE_ACTION:
#         action = _parse_action(event["action"])
#         changed = actionChooser.tryChooseAction(action, action_targets)

#     elif in_event_type == InEventType.CHOOSE_TARGET:
#         target = Square.from_list(event["target"])
#         changed = actionChooser.tryChooseTarget(target, action_targets)
#         if changed:
#             action_targets = {}

#     else:
#         assert False

#     if changed:
#         choice_event = {
#             "type": OutEventType.TURN_STATE_CHANGE.value,
#             "player": state.current_player,
#             "start": actionChooser.start,
#             "action": actionChooser.action,
#             "target": actionChooser.target,
#             "actionTargets": action_targets,
#             "nextChoice": actionChooser.next_choice,
#         }
#         await websocket.send(json.dumps(choice_event))

# print("Game over")



# For now we support at most one game at a time.
# this tracks the websocket of each connected player
# until both player are connected and we can start the game.
WEBSOCKETS: Dict[Player, WebSocketServerProtocol] = {}


async def handler(websocket: WebSocketServerProtocol) -> None:
    """
    Register player => websocket in a global registry.
    If we are the 2nd connecting player, start the game.
    Otherwise, wait forever for another player.

    Consumes a single message from the websocket queue containing the Player
    (north or south).  Future messages are handled inside the game task.
    """
    assert isinstance(websocket, WebSocketServerProtocol)
    join_message = await websocket.recv()
    join_event = json.loads(message)
    assert join_event["type"] == "join"

    player = Player(join_event["player"])
    assert player not in WEBSOCKETS
    WEBSOCKETS[player] = websocket
    print(f"{player} connected")

    try:
        if len(WEBSOCKETS) == 2:
            # both players are connected, so start the game.
            await play_one_game(WEBSOCKETS)
        else:
            # wait forever for the other player to connect
            # TODO:
            #   - needs to consume messages so we hear a disconnect
            #   - but then stop consuming messages once the game starts
            #   - and also exit when the game exits....
            await websocket.wait_closed()
    finally:
        del WEBSOCKETS[player]
        print(f"{player} disconnected")



async def main() -> None:
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
