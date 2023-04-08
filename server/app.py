#!/usr/bin/env python3

import asyncio
import json
from typing import Dict

from websockets.server import WebSocketServerProtocol, serve

from arena.server.constants import Player
from arena.server.game import play_one_game


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
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "join"

    player = Player(event["player"])
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
        # TODO:
        #   - try to close both connections & the ongoing game to get back to a clean state
        #   currently if only one player refreshes we are in trouble
        del WEBSOCKETS[player]
        print(f"{player} disconnected")


async def main() -> None:
    async with serve(handler, "", 8001):  # type: ignore
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
