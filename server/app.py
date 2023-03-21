#!/usr/bin/env python3

import asyncio
import json

import websockets

from arena.state import new_state, Player
from arena.server.terminal_ui import auto_place_tiles
from arena.server.game import _resolve_action
from arena.state import Action, OtherAction, Tile, Square


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


async def handler(websocket):
    print("New game")

    # initialize a new game
    # start with a hardcoded board for now
    # later random + place_tiles
    state = new_state()
    auto_place_tiles(Player.N, state)
    auto_place_tiles(Player.S, state)
    state.log("log line 1")
    state.log("log line 2")
    state.check_consistency()

    player = state.current_player()
    player_view = state.player_view(player)
    state_event = {"type": "state", "player_view": player_view.dict()}
    await websocket.send(json.dumps(state_event))
    await asyncio.sleep(0.5)

    async for message in websocket:
        # TODO
        #    - check it is from the correct player
        #    - check it is valid
        #    - if so, make move on board & send "board updated!" message to player
        #   worry about challenges & responses later
        event = json.loads(message)
        print(f"Received {event=}")
        assert event["type"] == "action"
        start = Square.from_list(event["start"])
        action = _parse_action(event["action"])
        target = Square.from_list(event["target"])

        _resolve_action(start, action, target, state)
        print("resolved action")

    print("Game over")


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
