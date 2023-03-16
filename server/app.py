#!/usr/bin/env python3

import asyncio
import json

import websockets

from arena.state import new_state, Player
from arena.server.terminal_ui import auto_place_tiles


async def handler(websocket):
    print("New game")

    # initialize a new game
    # start with a hardcoded board for now
    # later random + place_tiles
    state = new_state()
    auto_place_tiles(Player.N, state)
    auto_place_tiles(Player.S, state)
    state.check_consistency()

    player = state.current_player()
    player_view = state.player_view(player)
    state_event = {"type": "state", "player_view": player_view.json()}
    await websocket.send(json.dumps(state_event))
    await asyncio.sleep(0.5)

    async for message in websocket:
        assert False, "TODO: implement incoming messages"

    print("Game over")


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
