#!/usr/bin/env python3

import asyncio
import json

import websockets

from arena.server.state import new_state, Player
from arena.server.terminal_ui import auto_place_tiles
from arena.server.game import _resolve_action
from arena.server.state import Action, OtherAction, Tile, Square

from arena.server.action_chooser import ActionChooser


def _parse_action(action_string: str) -> Action:
    try:
        return OtherAction(action_string)
    except:
        pass

    try:
        return Tile(action_string)  # type: ignore
    except:
        pass

    raise ValueError(f"Unknown {action_string=}")


class InEventType(str, Enum):
    # values must match the JS event type strings
    CHOOSE_START: "CHOOSE_START"
    CHOOSE_ACTION: "CHOOSE_ACTION"
    CHOOSE_TARGET: "CHOOSE_TARGET"


class OutEventType(str, Enum):
    # values must match the JS event type strings

    # change in the persistent game state (tiles on board, tiles in hand, mana, etc)
    GAME_STATE_CHANGE: "GAME_STATE_CHANGE"

    # change in the player's selection (start, action, target)
    ACTION_CHOICE_CHANGE: "ACTION_CHOICE_CHANGE"


async def handler(websocket):
    print("New game")

    # initialize a new game
    # start with a hardcoded board for now
    # later random + place_tiles
    game_state = new_state()
    auto_place_tiles(Player.N, game_state)
    auto_place_tiles(Player.S, game_state)
    game_state.log("log line 1")
    game_state.log("log line 2")
    game_state.check_consistency()

    # should actually be per-person
    actionChooser = ActionChooser()
    actionChooser.beginChooseStart()

    player_view = game_state.player_view(game_state.current_player)
    state_event = {
        "type": OutEventType.GAME_STATE_CHANGE.value,
        "player_view": player_view.dict(),
    }
    await websocket.send(json.dumps(state_event))
    await asyncio.sleep(0.5)

    action_targets: Dict[Action, List[Square]] = {}

    async for message in websocket:
        # TODO
        #    - check it is from the correct player
        #    - check it is valid
        #    - if so, make move on board & send "board updated!" message to player
        #   worry about challenges & responses later
        in_event = json.loads(message)
        print(f"Received {in_event=}")
        in_event_type = InEventType(in_event["type"])

        if in_event_type == CHOOSE_START:
            start = Square.from_list(event["start"])
            changed = actionChooser.tryChooseStart(
                start, state.positions[state.current_player]
            )
            if changed:
                action_targets = valid_targets(start, game_state)

        elif in_event_type == CHOOSE_ACTION:
            action = _parse_action(event["action"])
            changed = actionChooser.tryChooseAction(action, valid_targets)

        elif in_event_type == CHOOSE_TARGET:
            target = Square.from_list(event["target"])
            changed = actionChooser.tryChooseTarget(action, valid_targets)
            if changed:
                action_targets = None

        else:
            assert False

        if changed:
            choice_event = {
                "type": ACTION_CHOICE_CHANGE.value,
                "player": game_state.current_player,
                "start": actionChooser.start,
                "action": actionChooser.action,
                "target": actionChooser.target,
                "action_targets": action_targets,
                "next_choice": actionChooser.next_choice,
            }
            await websocket.send(json.dumps(choice_event))

    print("Game over")


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
