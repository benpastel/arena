import asyncio
import json
from typing import Optional

from websockets.server import WebSocketServerProtocol

from server.state import State
from server.constants import Player, Square, Action, OutEventType, other_player


async def broadcast_state_changed(
    state: State, websockets: dict[Player, WebSocketServerProtocol]
) -> None:
    """Notify both players that the state changed."""
    async with asyncio.TaskGroup() as tg:
        for player, websocket in websockets.items():
            event = {
                "type": OutEventType.STATE_CHANGE.value,
                "playerView": state.player_view(player).dict(),
            }
            message = json.dumps(event)
            coroutine = websocket.send(message)
            tg.create_task(coroutine)


async def clear_selection(websockets: dict[Player, WebSocketServerProtocol]) -> None:
    """
    Remove any selection from both players' UI.
    """
    await broadcast_selection_changed(None, None, None, None, websockets)


async def broadcast_selection_changed(
    selecting_player: Optional[Player],
    start: Optional[Square],
    action: Optional[Action],
    target: Optional[Square],
    websockets: dict[Player, WebSocketServerProtocol],
) -> None:
    """
    Notify both players a selection changed.  See `notify_selection_changed` for details.
    """
    async with asyncio.TaskGroup() as tg:
        for websocket in websockets.values():
            coroutine = notify_selection_changed(
                selecting_player, start, action, target, websocket
            )
            tg.create_task(coroutine)


async def notify_selection_changed(
    selecting_player: Optional[Player],
    start: Optional[Square],
    action: Optional[Action],
    target: Optional[Square],
    websocket: WebSocketServerProtocol,
) -> None:
    """
    Notify one player that the selected action has changed.

    During a turn, we notify the current player multiple times as they make
    partial selections.

    If they opponent needs to respond, we notify them once
    so that we can display the selection before they respond.

    The game removes the selection from both players after the action is resolved
    by calling this with all None.
    """
    event = {
        "type": OutEventType.SELECTION_CHANGE.value,
        "player": selecting_player,
        "start": start,
        "action": action,
        "target": target,
    }
    message = json.dumps(event)
    await websocket.send(message)


async def broadcast_game_over(
    websockets: dict[Player, WebSocketServerProtocol],
    game_score: dict[Player, int],
) -> None:
    async with asyncio.TaskGroup() as tg:
        for player, websocket in websockets.items():
            us = game_score[player]
            them = game_score[other_player(player)]
            if us > them:
                msg = f"🎉🎉🎉 You won {us} to {them}. Nice! Try to win again!"
            elif us == them:
                msg = f"Tie! {us} - {them}. Wow, it finally happened! Cool!"
            else:
                msg = f"You lose {us} to {them}... but this game is mostly luck, so try again!"
            event = {
                "type": OutEventType.MATCH_CHANGE.value,
                "message": msg,
            }
            message = json.dumps(event)
            coroutine = websocket.send(message)
            tg.create_task(coroutine)
