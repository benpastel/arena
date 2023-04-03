from typing import Enum

from weakref import WeakKeyDictionary

from websockets.server import WebSocketServerProtocol

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

    # get an incrementing choice id so we can ignore old messages
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



async def choose_start(
    valid_starts: List[Square],
    websocket: WebSocketServerProtocol
) -> Square:
    # loop until we get a valid start square
    while True:
        data = await _get_choice(
            "Select a tile.",
            websocket
        )
        chosen = Square(
            row = data.get("row", -1),
            column = data.get("column", -1)
        )
        if chosen in valid_targets:
            return chosen
        else:
            print(f"Ignoring invalid start {chosen}")


# TODO: left off implement the other choose_X functions
# choose_action and choose_target will be harder because they return a union with cancel
# the tile-in-hand choices will need a representation





