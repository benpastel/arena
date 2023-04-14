#!/usr/bin/env python3

import asyncio
import json
from typing import Dict

from websockets.server import WebSocketServerProtocol, serve

from arena.server.constants import Player
from arena.server.game import play_one_game

# For now we don't use SSL because it's local-network only
# import ssl

# ssl_context = ssl.create_default_context()
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_NONE


# For now we support at most one game at a time.
# this tracks the websocket of each connected player
# until both players are connected and we can start the game.
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
    WEBSOCKETS[player] = websocket
    print(f"{player} connected")

    try:
        if len(WEBSOCKETS) == 2 and all(w.open for w in WEBSOCKETS.values()):
            # both players are connected, so start the game.
            await play_one_game(WEBSOCKETS)
        else:
            # wait forever for the other player to connect
            await websocket.wait_closed()
    finally:
        # whichever handler gets here closes both connections
        # both players will need to refresh to play a new game
        #
        # TODO: think the synchronization here through more carefully
        # and also what behavior you'd like if someone loses connection
        for websocket in WEBSOCKETS.values():
            await websocket.close()


async def main() -> None:
    # , ssl=ssl_context
    async with serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
