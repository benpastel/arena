from websockets.server import WebSocketServerProtocol
from typing import Iterable, AsyncIterable
import random

from server.constants import Action, Square, Tile, Response
from server.choices import (
    choose_action_or_square,
    choose_square_or_hand,
    choose_response,
    choose_exchange,
)


class Human:
    """
    Makes all choices by prompting a player over the websocket, and waiting for their response.
    """

    def __init__(self, websocket: WebSocketServerProtocol):
        self.websocket = websocket

    async def choose_action_or_square(
        self,
        possible_actions: list[Action],
        possible_squares: list[Square],
        prompt: str,
    ) -> Action | Square:
        return await choose_action_or_square(
            possible_actions,
            possible_squares,
            prompt,
            self.websocket,
        )

    async def choose_square_or_hand(
        self,
        possible_squares: list[Square],
        possible_hand_tiles: list[Tile],
        prompt: str,
    ) -> Square | Tile:
        return await choose_square_or_hand(
            possible_squares,
            possible_hand_tiles,
            prompt,
            self.websocket,
        )

    async def choose_response(
        self,
        possible_responses: list[Response | Tile],
        prompt: str,
    ) -> Response | Tile:
        return await choose_response(
            possible_responses,
            prompt,
            self.websocket,
        )

    async def choose_exchange(
        self,
        choices: list[Tile],
        prompt: str,
    ) -> Tile:
        return await choose_exchange(
            choices,
            prompt,
            self.websocket,
        )


class DummyWebsocket(WebSocketServerProtocol):
    """
    Implements the websocket send interface by doing nothing.

    This simplifies the game loop; we can always send notifications on the websocket
    without checking if it's a human or bot.
    """

    async def send(
        self, message: str | bytes | Iterable[str | bytes] | AsyncIterable[str | bytes]
    ) -> None:
        pass

    async def recv(self) -> str:
        raise NotImplementedError("DummyWebsocket should not receive messages")


class RandomBot:
    """
    Makes all choices with uniform random probability.
    """

    def __init__(self):
        self.websocket = DummyWebsocket()

    async def choose_action_or_square(
        self,
        possible_actions: list[Action],
        possible_squares: list[Square],
        prompt: str,
    ) -> Action | Square:
        choices: list[Action | Square] = possible_actions + possible_squares
        return random.choice(choices)

    async def choose_square_or_hand(
        self,
        possible_squares: list[Square],
        possible_hand_tiles: list[Tile],
        prompt: str,
    ) -> Square | Tile:
        choices: list[Square | Tile] = possible_squares + possible_hand_tiles
        return random.choice(choices)

    async def choose_response(
        self,
        possible_responses: list[Response | Tile],
        prompt: str,
    ) -> Response | Tile:
        return random.choice(possible_responses)

    async def choose_exchange(
        self,
        choices: list[Tile],
        prompt: str,
    ) -> Tile:
        return random.choice(choices)


# An agent is a human player or bot that makes choices
Agent = Human | RandomBot
