import json
from typing import List, cast
from weakref import WeakKeyDictionary

from websockets.server import WebSocketServerProtocol

from arena.server.constants import Tile, Action, OtherAction, Square, Response

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
    # TODO explain choice_id
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
    expected_choice_id = NEXT_CHOICE_ID.get(websocket, 0)
    NEXT_CHOICE_ID[websocket] = expected_choice_id + 1
    await send_prompt(prompt, websocket, expected_choice_id)

    # the websocket queue may have accumulated stale messages since we last recieved
    # wait in a loop to throw away any stale messages
    while True:
        message = await websocket.recv()
        event = json.loads(message)
        choice_id = int(event["choiceId"])

        if expected_choice_id == choice_id:
            return event["data"]
        elif choice_id < expected_choice_id:
            print(f"Ignored {choice_id=}; {expected_choice_id=}")
        else:
            assert (
                False
            ), f"{choice_id=} should never be greater than {expected_choice_id=}"


async def choose_action_or_square(
    possible_actions: List[Action],
    possible_squares: List[Square],
    prompt: str,
    websocket: WebSocketServerProtocol,
) -> Action | Square:
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
            tile = Tile(data["action"])
            if tile in possible_actions:
                return cast(Action, tile)
        except:
            pass

        # try parsing as an Other Action
        try:
            action = OtherAction(data["action"])
            if action in possible_actions:
                return action
        except:
            pass

        # it's not valid; get a new choice
        print(f"Ignoring invalid choice {data=}")


async def choose_square_or_hand(
    possible_squares: List[Square],
    possible_hand_tiles: List[Tile],
    prompt: str,
    websocket: WebSocketServerProtocol,
) -> Square | Tile:
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
            tile = Tile(data["tile"])
            if tile in possible_hand_tiles:
                return tile
        except:
            pass

        # it's not valid; get a new choice
        print(f"Ignoring invalid choice {data=}")


async def choose_response(
    possible_responses: List[Response], prompt: str, websocket: WebSocketServerProtocol
) -> Response:
    # loop until we get a valid response
    while True:
        data = await _get_choice(
            prompt,
            websocket,
        )
        # try parsing as a response
        # TODO: make sure javascript fields match
        try:
            response = Response(data["response"])
            if response in possible_responses:
                return response
        except:
            pass

        # it's not valid; get a new choice
        print(f"Ignoring invalid choice {data=}")
