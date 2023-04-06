from typing import Enum
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
# It's a WeakKeyDictionary so we don't keep a reference to old websockets.
NEXT_CHOICE_ID: WeakKeyDictionary[WebSocketServerProtocol, int] = {}


async def _get_choice(
    websocket: WebSocketServerProtocol,
    prompt: str
) -> dict
    """
    Prompts the player for a choice
    and returns the data from their response
    ignoring all other messages
    """

    # increment choice id
    # we use this to ignore old messages
    expected_choice_id = NEXT_CHOICE_ID.get(websocket, 0)
    NEXT_CHOICE_ID[websocket] = expected_choice_id + 1

    # prompt the player for this choice
    # TODO share "type"=="prompt" with other prompts like "waiting for opponent to X"
    prompt_event = {
        "type": "prompt",
        "choice_id": expected_choice_id,
        "prompt": prompt
    }
    await websocket.send(json.dumps(prompt_event))

    while True:
        message = await websocket.recv()
        event = json.loads(message)
        choice_id = int(event["choice_id"])

        if expected_choice_id == choice_id:
            return event["data"]
        elif choice_id < expected_choice_id:
            print(f"Ignored {choice_id=}; {expected_choice_id=}")
        else:
            assert False, f"{choice_id=} should never be greater than {expected_choice_id=}"



async def choose_action_or_square(
    valid_actions: List[Action],
    valid_squares: List[Square],
    websocket: WebSocketServerProtocol,
    prompt: str
) -> Action | Square:
    # loop until we get a valid action or square
    # TODO: send the list of possibilities to the player to highlight instead of current method?
    while True:
        data = await _get_choice(
            websocket
            prompt,
        )
        # try parsing as a square
        square = Square(
            row = data.get("row", -1),
            column = data.get("column", -1)
        )
        if square in valid_squares:
            return square

        # try parsing as a Tile Action
        # TODO: make sure javascript keys match these
        try:
            action = Tile(data["action"])
            if action in valid_actions:
                return action
        except:
            pass

        # try parsing as an Other Action
        try:
            action = OtherAction(data["action"])
            if action in valid_actions:
                return action
        except:
            pass

        # it's not valid; get a new choice
        print(f"Ignoring invalid choice {data=}")


async def choose_square_or_hand(
    valid_squares: List[Square],
    valid_hand_tiles: List[Tile],
    websocket: WebSocketServerProtocol,
    prompt: str
) -> Square | Tile:
    # loop until we get a valid square or hand tile
    # TODO: send the list of possibilities to the player to highlight
    while True:
        data = await _get_choice(
            websocket
            prompt,
        )
        # try parsing as a square
        square = Square(
            row = data.get("row", -1),
            column = data.get("column", -1)
        )
        if square in valid_squares:
            return square

        # try parsing as a Tile
        # TODO: make sure javascript keys match these
        try:
            tile = Tile(data["tile"])
            if tile in valid_hand_tiles:
                return tile
        except:
            pass

        # it's not valid; get a new choice
        print(f"Ignoring invalid choice {data=}")

async def choose_response(
    possible_responses: List[Response],
    websocket: WebSocketServerProtocol,
    prompt: str
) -> Response:
    # loop until we get a valid response
    while True:
        data = await _get_choice(
            websocket
            prompt,
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
