import random

from server.constants import (
    Action,
    ActionAndTarget,
    Square,
    Tile,
    Response,
    OtherAction,
)
from server.seat import Seat, DummySeat
from server.choices import (
    choose_action_or_square,
    choose_square_or_hand,
    choose_response,
    choose_exchange,
)


class Human:
    """
    Makes all choices by prompting a player through their seat, and waiting for their response.
    """

    def __init__(self, seat: Seat):
        self.seat = seat

    async def choose_action_or_square(
        self,
        possible_actions: list[Action],
        possible_squares: list[Square],
        prompt: str,
        true_action_hint: Action | None,
        targets: dict[Action, list[Square]] | None = None,
    ) -> Action | Square | ActionAndTarget:
        return await choose_action_or_square(
            possible_actions,
            possible_squares,
            prompt,
            self.seat,
            targets,
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
            self.seat,
        )

    async def choose_response(
        self,
        possible_responses: list[Response | Tile],
        prompt: str,
        true_response_hint: Tile | None,
    ) -> Response | Tile:
        return await choose_response(
            possible_responses,
            prompt,
            self.seat,
        )

    async def choose_exchange(
        self,
        choices: list[Tile],
        prompt: str,
    ) -> Tile:
        return await choose_exchange(
            choices,
            prompt,
            self.seat,
        )


class RandomBot:
    """
    Chooses true actions when possible; otherwise lies with fixed probability.
    Challanges with fixed probability.
    """

    def __init__(self):
        self.seat = DummySeat()
        self.truth_prob = 2 / 3
        self.challenge_prob = 1 / 4

    async def choose_action_or_square(
        self,
        possible_actions: list[Action],
        possible_squares: list[Square],
        prompt: str,
        true_action_hint: Action | None,
        targets: dict[Action, list[Square]] | None = None,
    ) -> Action | Square:
        # if there's a true, nonmove action, always take it
        if true_action_hint and true_action_hint in possible_actions:
            return true_action_hint

        # if there's no action, return a square
        if not possible_actions:
            return random.choice(possible_squares)

        # otherwise, randomly decide between moving and a lying action
        lie_actions = [a for a in possible_actions if a != OtherAction.MOVE]

        if random.random() < self.truth_prob:
            return OtherAction.MOVE
        else:
            return random.choice(lie_actions)

    async def choose_square_or_hand(
        self,
        possible_squares: list[Square],
        possible_hand_tiles: list[Tile],
        prompt: str,
    ) -> Square | Tile:
        # choose randomly
        choices: list[Square | Tile] = possible_squares + possible_hand_tiles
        return random.choice(choices)

    async def choose_response(
        self,
        possible_responses: list[Response | Tile],
        prompt: str,
        true_response_hint: Tile | None,
    ) -> Response | Tile:
        # if there's a true Tile response reflecting an attack, always choose it
        if true_response_hint in possible_responses:
            return true_response_hint

        # sometimes challenge
        if (
            Response.CHALLENGE in possible_responses
            and random.random() < self.challenge_prob
        ):
            return random.choice(possible_responses)

        # sometimes lie about reflecting
        lie_responses = [
            r
            for r in possible_responses
            if r != true_response_hint and isinstance(r, Tile)
        ]
        if lie_responses and random.random() > self.truth_prob:
            return random.choice(lie_responses)

        # otherwise, accept
        assert Response.ACCEPT in possible_responses
        return Response.ACCEPT

    async def choose_exchange(
        self,
        choices: list[Tile],
        prompt: str,
    ) -> Tile:
        # choose randomly
        return random.choice(choices)


# An agent is a human player or bot that makes choices
Agent = Human | RandomBot
