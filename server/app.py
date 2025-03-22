#!/usr/bin/env python3

import asyncio
import json
import os
import signal

from websockets.server import WebSocketServerProtocol, serve

from server.constants import Player
from server.game import play_one_game
from server.notify import broadcast_game_over
from server.agents import Agent, Human, RandomBot


# For now we support at most one game at a time.
# this tracks the websocket of each connected player
# until both players are connected and we can start the game.
PLAYERS: dict[Player, Agent] = {}

# URL player parameter for playing against the AI
SOLO_PLAYER = "solo"


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

    if event["player"] == SOLO_PLAYER:
        # in solo mode, the player is south and the AI is north
        player = Player.S
        PLAYERS[player] = Human(websocket)
        PLAYERS[Player.N] = RandomBot()
    else:
        # in pvp, the player is the one specified in the url
        # wait for the other player to connect
        player = Player(event["player"])
        PLAYERS[player] = Human(websocket)

    # and double check whether DummyWebsocket should support wait_closed, open, etc.
    print(f"{player} connected")

    try:
        if len(PLAYERS) == 2 and all(w.websocket.open for w in PLAYERS.values()):
            # both players are connected, so start the match.
            print(f"New match with {PLAYERS}")
            match_score = {Player.N: 0, Player.S: 0}
            while True:
                game_score = await play_one_game(match_score.copy(), PLAYERS)
                for player, points in game_score.items():
                    match_score[player] += points

                # let the player's board redraw before sending the game over alert
                await asyncio.sleep(0.5)

                await broadcast_game_over(PLAYERS, game_score)
        else:
            # wait forever for the other player to connect
            # the other player's handler will run the game and close the connection
            print(f"{player} waiting for other player")
            await websocket.wait_closed()
    finally:
        # whichever handler gets here closes both connections
        # both players will need to refresh to play a new game
        #
        # TODO: think the synchronization here through more carefully
        # and also what behavior you'd like if someone loses connection
        for agent in PLAYERS.values():
            if isinstance(agent, Human):
                await agent.websocket.close()


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
