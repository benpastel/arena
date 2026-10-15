"""
Move clocks.

Each decision has an allowance: longer for choosing your action, shorter for everything
else (whether to challenge, what to lose, the exchange...).  Time past the allowance
comes out of a reserve that lasts the game.  Once both are gone the game decides for
the player, with the defaults in game.py, and carries on; nobody loses on time.

The clock is the game's, per table, but the game's functions all reach it through
`decide`, which finds the current game's clock in a context variable: each match runs
in its own task, so each sees its own.
"""

import asyncio
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

from server.constants import OutEventType, Player
from server.seat import Seat

T = TypeVar("T")


@dataclass(frozen=True)
class TimeControl:
    reserve: float
    main: float
    minor: float


# "unlimited" has no clock at all
TIME_CONTROLS = {
    "fast": TimeControl(reserve=60, main=10, minor=5),
    "medium": TimeControl(reserve=120, main=20, minor=10),
    "slow": TimeControl(reserve=240, main=40, minor=20),
}
UNLIMITED = "unlimited"
TIME_MODES = (*TIME_CONTROLS, UNLIMITED)

# a click sent just before the deadline still counts, if it's this late in arriving
LAG_GRACE = 0.5


class Clock:
    def __init__(self, control: TimeControl, seats: dict[Player, Seat]):
        self.control = control
        self.seats = seats
        self.reserve = {player: control.reserve for player in Player}

    async def decide(
        self,
        player: Player,
        main: bool,
        choice: Awaitable[T],
        default: Callable[[], T],
    ) -> T:
        allowance = self.control.main if main else self.control.minor
        started = time.monotonic()
        await self.send(player, allowance)
        try:
            async with asyncio.timeout(allowance + self.reserve[player] + LAG_GRACE):
                result = await choice
        except TimeoutError:
            self.reserve[player] = 0
            # their last prompt asked for a choice that's no longer wanted
            await self.seats[player].send(
                {"type": OutEventType.PROMPT, "choiceId": 0, "prompt": ""}
            )
            result = default()
        else:
            over = time.monotonic() - started - allowance
            self.reserve[player] = max(0.0, self.reserve[player] - max(0.0, over))
        await self.send(None, 0)
        return result

    async def send(self, running: Player | None, allowance: float) -> None:
        """
        Both reserves, and whose clock is running: their allowance, then their reserve,
        count down from now.  Times are in epoch ms; see Seat.attach for `sent`.
        """
        now = time.time() * 1000
        event = {
            "type": OutEventType.CLOCK,
            "reserve": {player.value: self.reserve[player] * 1000 for player in Player},
            "running": running,
            "allowanceEnds": now + allowance * 1000,
            "sent": now,
        }
        for seat in self.seats.values():
            await seat.send(event)


_clock: ContextVar[Clock | None] = ContextVar("clock", default=None)


def start_clock(time_mode: str, seats: dict[Player, Seat]) -> Clock | None:
    """A fresh clock for this game, with the reserves full; None if unlimited."""
    control = TIME_CONTROLS.get(time_mode)
    clock = Clock(control, seats) if control else None
    _clock.set(clock)
    return clock


async def decide(
    player: Player,
    main: bool,
    choice: Awaitable[T],
    default: Callable[[], T],
) -> T:
    """
    Wait for `player` to make `choice` on the clock, or take `default()` if they run
    out of time.  `main` is the choice of action; everything else gets the minor
    allowance.
    """
    clock = _clock.get()
    if clock is None:
        return await choice
    return await clock.decide(player, main, choice, default)
