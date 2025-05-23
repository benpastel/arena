import json
from typing import cast
from weakref import WeakKeyDictionary
from contextlib import asynccontextmanager

from websockets.server import WebSocketServerProtocol

from server.constants import (
    Tile,
    Action,
    OtherAction,
    Square,
    Response,
    OutEventType,
)

# Generally incoming messages are invalid unless we've prompted for them.
# websockets keeps incoming messages in a FIFO queue, but generally all messages
# are invalid unless we've prompted for something specific.
#
# For each websocket, we use an incrementing count as an ID
# All messages with other choice ids are ignored, so we can ignore messages from
# before our prompt.
#
# Weak references so we don't keep old websockets alive.
NEXT_CHOICE_ID: WeakKeyDictionary[WebSocketServerProtocol, int] = WeakKeyDictionary()


async def send_prompt(
    prompt: str, websocket: WebSocketServerProtocol, choice_id: int = 0
) -> None:
    """
    Update the player's prompt.

    If we need them to make a choice, choice_id should be set to an incrementing ID
    so that we can ignore old clicks from before this prompt.
    We add alert emoji around the prompt.

    If we don't need them to make a choice, we keep choice_id = 0.  We add
    hourglass emoji around the prompt.
    """
    if choice_id > 0:
        prompt = f"⚠️⚠️⚠️<br>{prompt}<br>⚠️⚠️⚠️"
    else:
        prompt = f"⌛⌛⌛<br>{prompt}<br>⌛⌛⌛"

    event = {"type": "PROMPT", "choiceId": choice_id, "prompt": prompt}
    await websocket.send(json.dumps(event))


async def _get_choice(prompt: str, websocket: WebSocketServerProtocol) -> dict:
    """
    Prompts the player for a choice
    and returns the data from their response
    ignoring all other messages
    """

    # increment choice id
    # we use this to ignore old messages
    expected_choice_id = NEXT_CHOICE_ID.get(websocket, 1)
    NEXT_CHOICE_ID[websocket] = expected_choice_id + 1
    await send_prompt(prompt, websocket, expected_choice_id)

    # the websocket queue may have accumulated stale messages since we last recieved
    # wait in a loop to throw away any stale messages
    while True:
        message = await websocket.recv()
        event = json.loads(message)
        if "choiceId" not in event:
            print(f"Ignored {event=}")
            continue
        choice_id = int(event["choiceId"])

        if expected_choice_id == choice_id:
            return event["data"]
        elif choice_id < expected_choice_id:
            print(f"Ignored {choice_id=}; {expected_choice_id=}")
        else:
            assert (
                False
            ), f"{choice_id=} should never be greater than {expected_choice_id=}"


async def _send_highlights(
    websocket: WebSocketServerProtocol,
    squares: list[Square],
    actions: list[Action | Response],
    hand_tiles: list[Tile],
    board_tiles: list[Tile],
):
    event = {
        "type": OutEventType.HIGHLIGHT_CHANGE,
        "squares": squares,
        "actions": actions,
        "handTiles": hand_tiles,
        "boardTiles": board_tiles,
    }
    await websocket.send(json.dumps(event))


@asynccontextmanager
async def _highlighted(
    websocket: WebSocketServerProtocol,
    squares: list[Square] = [],
    actions: list[Action | Response] = [],
    hand_tiles: list[Tile] = [],
    board_tiles: list[Tile] = [],
):
    """Sends a list of highlighted options to the player.  Clears highlights when done."""
    await _send_highlights(websocket, squares, actions, hand_tiles, board_tiles)
    yield
    # clear highlights in UI by highlighting empty lists
    await _send_highlights(websocket, [], [], [], [])


async def choose_action_or_square(
    possible_actions: list[Action],
    possible_squares: list[Square],
    prompt: str,
    websocket: WebSocketServerProtocol,
) -> Action | Square:
    async with _highlighted(
        websocket,
        actions=cast(list[Action | Response], possible_actions),
        squares=possible_squares,
    ):
        # loop until we get a valid action or square
        while True:
            data = await _get_choice(
                prompt,
                websocket,
            )
            # try parsing as a square
            square = Square(row=data.get("row", -1), col=data.get("column", -1))
            if square in possible_squares:
                return square

            # try parsing as a Tile Action
            try:
                tile = Tile(data["button"])
                if tile in possible_actions:
                    return cast(Action, tile)
            except:
                pass

            # try parsing as an Other Action
            try:
                action = OtherAction(data["button"])
                if action in possible_actions:
                    return action
            except:
                pass

            # it's not valid; get a new choice
            print(
                f"Ignoring invalid choice {data=}, {possible_actions=}, {possible_squares=}"
            )


async def choose_square_or_hand(
    possible_squares: list[Square],
    possible_hand_tiles: list[Tile],
    prompt: str,
    websocket: WebSocketServerProtocol,
) -> Square | Tile:
    async with _highlighted(
        websocket, squares=possible_squares, hand_tiles=possible_hand_tiles
    ):
        # loop until we get a valid square or hand tile
        while True:
            data = await _get_choice(
                prompt,
                websocket,
            )
            # try parsing as a square
            square = Square(row=data.get("row", -1), col=data.get("column", -1))
            if square in possible_squares:
                return square

            # try parsing as a Tile
            try:
                tile = Tile(data["handTile"])
                if tile in possible_hand_tiles:
                    return tile
            except:
                pass

            # it's not valid; get a new choice
            print(
                f"Ignoring invalid choice {data=}, {possible_squares=}, {possible_hand_tiles=}"
            )


async def choose_response(
    possible_responses: list[Response | Tile],
    prompt: str,
    websocket: WebSocketServerProtocol,
) -> Response | Tile:
    async with _highlighted(
        websocket, actions=cast(list[Action | Response], possible_responses)
    ):
        # loop until we get a valid response
        while True:
            data = await _get_choice(
                prompt,
                websocket,
            )
            # try parsing as a Response
            try:
                response = Response(data["button"])
                if response in possible_responses:
                    return response
            except:
                pass

            # try parsing as a Tile
            try:
                tile = Tile(data["button"])
                if tile in possible_responses:
                    return tile
            except:
                pass

            # it's not valid; get a new choice
            print(f"Ignoring invalid choice {data=}, {possible_responses=}")


async def choose_exchange(
    choices: list[Tile],
    prompt: str,
    websocket: WebSocketServerProtocol,
) -> Tile:
    async with _highlighted(websocket, board_tiles=choices):
        # loop until we get a valid response
        while True:
            data = await _get_choice(
                prompt,
                websocket,
            )
            # try parsing as a Tile
            try:
                tile = Tile(data["boardTile"])
                if tile in choices:
                    return tile
            except:
                pass

            # it's not valid; get a new choice
            print(f"Ignoring invalid choice {data=}, {choices=}")
