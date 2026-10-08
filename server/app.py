#!/usr/bin/env python3

import asyncio
import json
import os
import signal
from http import HTTPStatus

from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol, serve

from server.lobby import Lobby, User


LOBBY = Lobby()


async def handler(websocket: WebSocketServerProtocol) -> None:
    """
    One browser tab's connection.

    The first message must be a hello identifying the user; every message after that
    is a lobby request or a click in their game.  When the socket closes the user
    keeps their seat, so they can reconnect into it.
    """
    user: User | None = None
    try:
        async for message in websocket:
            try:
                event = json.loads(message)
                if user is None:
                    if event.get("type") == "hello":
                        user = await LOBBY.hello(
                            websocket, event.get("playerId"), event.get("name")
                        )
                    continue
                await LOBBY.handle(user, event)
            except ConnectionClosed:
                raise
            except Exception as e:
                # a malformed message shouldn't drop the connection
                print(f"Ignored {message=}: {e!r}")
    except ConnectionClosed:
        pass
    finally:
        if user is not None:
            await LOBBY.disconnect(user, websocket)


async def health_check(path: str, request_headers: object) -> tuple | None:
    # plain HTTP probe for render's health check; anything else proceeds to the websocket handshake
    if path == "/healthz":
        return HTTPStatus.OK, [], b"OK\n"
    return None


async def main() -> None:
    # render sends SIGTERM when shutting down an instance; listen & exit gracefully
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    port = int(os.environ.get("PORT", "8001"))
    print(f"Serving websocket server on port {port}.")

    reaper = asyncio.create_task(LOBBY.reap_forever())
    async with serve(handler, "", port, process_request=health_check):
        await stop
    reaper.cancel()


if __name__ == "__main__":
    asyncio.run(main())
