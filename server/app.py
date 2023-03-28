#!/usr/bin/env python3

import asyncio
import json
from enum import Enum
from typing import List, Dict, Any

import websockets

from arena.server.state import new_state, Player
from arena.server.actions import valid_targets
from arena.server.terminal_ui import auto_place_tiles

# from arena.server.game import _resolve_action
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
    CHOOSE_START = "CHOOSE_START"
    CHOOSE_ACTION = "CHOOSE_ACTION"
    CHOOSE_TARGET = "CHOOSE_TARGET"


class OutEventType(str, Enum):
    # values must match the JS event type strings

    # change in the persistent game state (tiles on board, tiles in hand, mana, etc)
    GAME_STATE_CHANGE = "GAME_STATE_CHANGE"

    # change in the player's selection (start, action, target)
    TURN_STATE_CHANGE = "TURN_STATE_CHANGE"


# game id => the websockets for each player
WEBSOCKETS: Dict[int, Dict[Player, Any]] = {}

# game id => the between-turn state of the game (tiles, money, etc)
GAME_STATES: Dict[int, GameState] = {}

# game id => the within-turn state of the game (actions selected so far, challenge decisions, etc)
TURN_STATES: Dict[int, TurnState] = {}

# for now hardcode at most one game running at a time
GAME_ID = 0





async def playHandler() -> None:
    """
    Both players have separate handler threads.

    To simplify synchronization we only progress the game in this thread,
    while the other thread blocks.
    """
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
        "playerView": player_view.dict(),
    }
    await websocket.send(json.dumps(state_event))
    await asyncio.sleep(0.5)

    # currently valid actions => targets
    # based on both the game state and the actionChooser state
    action_targets: Dict[Action, List[Square]] = {}

    async for message in websocket:
        # TODO
        #    - check it is from the correct player
        #    - check it is valid
        #    - if so, make move on board & send "board updated!" message to player
        #   worry about challenges & responses later
        event = json.loads(message)
        print(f"Received {event=}")
        in_event_type = InEventType(event["type"])

        if in_event_type == InEventType.CHOOSE_START:
            start = Square.from_list(event["start"])
            changed = actionChooser.tryChooseStart(
                start, game_state.positions[game_state.current_player]
            )
            if changed:
                action_targets = valid_targets(start, game_state)

        elif in_event_type == InEventType.CHOOSE_ACTION:
            action = _parse_action(event["action"])
            changed = actionChooser.tryChooseAction(action, action_targets)

        elif in_event_type == InEventType.CHOOSE_TARGET:
            target = Square.from_list(event["target"])
            changed = actionChooser.tryChooseTarget(target, action_targets)
            if changed:
                action_targets = {}

        else:
            assert False

        if changed:
            choice_event = {
                "type": OutEventType.TURN_STATE_CHANGE.value,
                "player": game_state.current_player,
                "start": actionChooser.start,
                "action": actionChooser.action,
                "target": actionChooser.target,
                "actionTargets": action_targets,
                "nextChoice": actionChooser.next_choice,
            }
            await websocket.send(json.dumps(choice_event))

    print("Game over")




async def handler(websocket: Any) -> None:
    """
    Register the player => websocket in the global registry
    wait for both players
    then start playing
    """
    join_message = await websocket.recv()
    join_event = json.loads(message)
    assert join_event["type"] == "join"

    player = Player(join_event["player"])

    # eventually we'll need to handle reconnecting
    # right now just end the game and delete the websocket
    assert player not in WEBSOCKETS
    WEBSOCKETS[player] = websocket

    print(f"{player} connected")
    try:
        async for message in websocket:
            if len(WEBSOCKETS) != 2:
                print(f"{player} waiting until both players connected")
            else
                print(f"{player} starting game")
                play_one_game(player)
                break

    finally:
        del WEBSOCKETS[player]
        print(f"{player} disconnected")






async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
