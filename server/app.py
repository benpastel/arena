#!/usr/bin/env python3

import asyncio
import json
import os
import signal

from websockets.server import WebSocketServerProtocol, serve

from server.constants import Player
from server.game import play_one_match
from server.agents import Agent, Human, RandomBot


# URL player parameter for playing against the AI
SOLO_PLAYER = "solo"

# PVP_PLAYERS is a dict from joined players (NORTH or SOUTH) to the human agent.
# At most 1 PVP game at a time (see `handler` docstring for explanation)
PVP_PLAYERS: dict[Player, Agent] = {}


async def handler(websocket: WebSocketServerProtocol) -> None:
    """
    Supports:
        - any number of solo games (player vs AI)
        - at most 1 PVP game (2 human players)

    When a new websocket connects, it could be:
        - a player creating a solo game
        - the first player joining a PVP game
        - the second player joining a PVP game

    If the first player joins a PVP game, just register their websocket and then wait forever;
    the actual game will run in the second player's handler.

    2nd player to connect determines whether the game uses the default configuration, or a randomized configuration,
    via the `randomize` parameter.

    Consumes a single message from the websocket queue containing the Player
    (north, south, or solo).  Future messages are handled inside the game task.

    `play_one_match` makes a best effort to close the websocket when a player disconnects;
    if it fails, we rely on the default timeouts in the `serve` caller to close the connection.

    2nd player to connect
    """
    assert isinstance(websocket, WebSocketServerProtocol)
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "join"
    assert event["randomize"] in [True, False]
    randomize = event["randomize"]

    if event["player"] == SOLO_PLAYER:
        # in solo mode, the player is south and the AI is north
        players: dict[Player, Agent] = {
            Player.S: Human(websocket),
            Player.N: RandomBot(),
        }
        await play_one_match(players, randomize)
        return

    # in pvp, the player is the one specified in the url
    # overwrite the existing websocket/agent if it exists
    player = Player(event["player"])
    PVP_PLAYERS[player] = Human(websocket)

    if len(PVP_PLAYERS) == 2 and all(w.websocket.open for w in PVP_PLAYERS.values()):
        print(f"{player} connected; starting match")
        await play_one_match(PVP_PLAYERS, randomize)
        return
    else:
        print(f"{player} waiting for other player")
        await websocket.wait_closed()


async def main() -> None:
    # heroku sends SIGTERM when shutting down a dyno; listen & exit gracefully
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    port = int(os.environ.get("PORT", "8001"))
    print(f"Serving websocket server on port {port}.")

    async with serve(handler, "", port):
        await stop


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
