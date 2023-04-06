import asyncio

from websockets.server import WebSocketServerProtocol

from arena.server.state import State
from arena.server.constants import Player, Square, Action, OutEventType


async def notify_state_changed(
    state: State, websockets: Dict[Player, WebSocketServerProtocol]
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


async def notify_selection_changed(
    selecting_player: Player,
    start: Optional[Square],
    action: Optional[Action],
    target: Optional[Square],
    actions_and_targets: Dict[Action, List[Square]],
    websocket: WebSocketServerProtocol,
) -> None:
    """
    Notify one player that the selected action has changed.

    During a turn, we notify the current player multiple times as they make
    partial selections.

    If they opponent needs to respond, we notify them once
    so that we can display the selection before they respond.
    """
    event = {
        "type": OutEventType.SELECTION_CHANGE.value,
        "player": selecting_player,
        "start": start,
        "action": action,
        "target": target,
        "actionTargets": actions_and_targets,
    }
    message = json.dumps(event)
    await websocket.send(message)
