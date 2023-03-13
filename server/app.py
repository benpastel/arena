#!/usr/bin/env python3

import asyncio
import json

import websockets

from arena.web.connect4 import Connect4


async def handler(websocket):
    print("New game")

    # Initialize a Connect Four game.
    game = Connect4()

    async for message in websocket:
        in_event = json.loads(message)
        assert in_event["type"] == "play"
        column = in_event["column"]
        player = game.current_player

        try:
            row = game.play(player, column)
        except:
            error_event = {"type": "error", "message": "invalid move"}
            await websocket.send(json.dumps(error_event))
            continue

        move_event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row,
        }
        await websocket.send(json.dumps(move_event))
        await asyncio.sleep(0.5)

        if game.last_player_won:
            win_event = {
                "type": "win",
                "player": game.last_player,
            }
            await websocket.send(json.dumps(win_event))
            break

    print("Game over")


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
