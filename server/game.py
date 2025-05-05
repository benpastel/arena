from typing import Optional, cast
from random import shuffle
import asyncio

from server.agents import Agent, Human
from server.actions import (
    valid_targets,
    take_action,
    reflect_action,
    grapple_end_square,
)
from server.state import new_state, State
from server.constants import (
    Player,
    Square,
    GameResult,
    Action,
    Tile,
    OtherAction,
    Response,
    other_player,
)
from server.choices import send_prompt
from server.notify import (
    broadcast_state_changed,
    notify_selection_changed,
    broadcast_selection_changed,
    clear_selection,
    broadcast_game_over,
)


async def _resolve_bonus(
    state: State,
    players: dict[Player, Agent],
) -> None:
    """Give a player bonus for starting their turn on the bonus square"""
    player = state.maybe_player_at(state.bonus_position)
    if state.current_player != player:
        # current player does not get the bonus
        return

    revealed = 0
    for _ in range(state.bonus_reveal):
        revealed += state.reveal_unused()

    state.log(
        f"{player.format_for_log()} starts turn on bonus square: +${state.bonus_amount}, revealed {revealed} unused tiles"
    )
    state.coins[player] += state.bonus_amount
    await broadcast_state_changed(state, players)


async def _move_x2(
    square: Square,
    state: State,
    players: dict[Player, Agent],
) -> None:
    """Allow the player to move the x2 highlight."""
    player = state.player_at(square)
    await send_prompt(
        "Waiting for opponent to move the ×2.",
        players[other_player(player)].websocket,
    )
    choices: list[Action] = [t for t in Tile if t != state.x2_tile and t != Tile.HIDDEN]
    choice = await players[player].choose_action_or_square(
        choices,
        [],
        "Move the ×2 to a different action.",
        true_action_hint=None,
    )
    assert isinstance(choice, Tile)
    state.x2_tile = choice
    state.log(f"{player.format_for_log()} moved ×2 to {choice}")

    await broadcast_state_changed(state, players)


async def _resolve_exchange(
    square: Square,
    state: State,
    players: dict[Player, Agent],
) -> None:
    """Allow a player to exchange with a exchange square"""
    player = state.player_at(square)
    exchange_index = state.exchange_positions.index(square)
    tile_on_board_index = state.positions[player].index(square)

    # player can now see the exchange position
    state.exchange_tiles_revealed[player][exchange_index] = True

    await broadcast_state_changed(state, players)
    await send_prompt(
        "Waiting for opponent to exchange tiles.",
        players[other_player(player)].websocket,
    )

    # if they could, other player can no longer see the exchange position or tile
    # because it may have change
    state.exchange_tiles_revealed[other_player(player)][exchange_index] = False
    state.tiles_on_board_revealed[player][tile_on_board_index] = False

    old_tile = state.tile_at(square)
    exchange_choices = state.exchange_tiles[exchange_index] + [old_tile]
    choice = await players[player].choose_exchange(
        exchange_choices,
        "Exchange tiles, or keep your current tile.",
    )

    if choice != old_tile:
        # they swapped with a exchange tile
        state.tiles_on_board[player][tile_on_board_index] = choice
        state.exchange_tiles[exchange_index].remove(choice)
        state.exchange_tiles[exchange_index].append(old_tile)

        # shuffle to hide which tile they placed
        shuffle(state.exchange_tiles[exchange_index])

    state.log(f"{player.format_for_log()} may have exchanged tiles.")


async def _resolve_smite(
    state: State,
    player: Player,
    players: dict[Player, Agent],
    target: Square,
) -> None:
    state.coins[player] -= state.smite_cost
    state.log(
        f"{player.format_for_log()} smites ⚡ {target.format_for_log()} for ${state.smite_cost}"
    )

    await _lose_tile(target, state, players)
    await clear_selection(players)


async def _check_special_square(
    end_square: Square, state: State, players: dict[Player, Agent]
) -> None:
    """
    One of the players moved onto end_square, either directly or as side effect of an action;
    If it's a special square, resolve it.
    """
    if state.x2_tile is not None and end_square == state.bonus_position:
        await _move_x2(end_square, state, players)

    if end_square in state.exchange_positions:
        await _resolve_exchange(end_square, state, players)


async def _resolve_action(
    start: Square,
    action: Action,
    target: Square,
    state: State,
    players: dict[Player, Agent],
    reflect: bool = False,
) -> None:
    if state.x2_tile == action:
        repeats = 2
        x2_msg = "2X "
    else:
        repeats = 1
        x2_msg = ""

    # `hits` is a possibly-empty list of tiles hit by the action
    if reflect:
        hits = reflect_action(start, action, target, state)
        state.log(f"{state.other_player.format_for_log()} reflects {x2_msg}{action}")
    else:
        hits = take_action(start, action, target, state)
        state.log(f"{state.current_player.format_for_log()} uses {x2_msg}{action}")

    for repeat in range(repeats):
        if repeats > 1 and hits:
            state.log(f"{repeat + 1} / {repeats} - ")

        for hit in hits:
            await _lose_tile(hit, state, players)

        await clear_selection(players)

    # we may have moved onto a special square
    if action in (
        OtherAction.MOVE,
        Tile.FLOWER,
        Tile.BIRD,
        Tile.TRICKSTER,
        Tile.HARVESTER,
        Tile.RAM,
        Tile.BACKSTABBER,
    ):
        await _check_special_square(target, state, players)

    # hook may have pulled someone onto one
    if action == Tile.HOOK:
        if reflect:
            # player moved
            end_square = grapple_end_square(target, start, obstructions=[])
        else:
            # enemy moved
            end_square = grapple_end_square(start, target, obstructions=[])
        assert end_square is not None
        await _check_special_square(end_square, state, players)

    # thief swaps positions, which might moveither player onto one
    if action == Tile.THIEF:
        await _check_special_square(start, state, players)
        await _check_special_square(target, state, players)


async def _select_action(
    state: State, players: dict[Player, Agent]
) -> tuple[Square, Action, Square]:
    """
    Prompt the player to choose the action for their turn.

    Returns:
        - square of the tile that's taking the action
        - the action
        - target square of the action
    """
    await send_prompt(
        "Waiting for opponent to select their action.",
        players[state.other_player].websocket,
    )
    current_agent = players[state.current_player]

    possible_starts = state.positions[state.current_player]
    assert 1 <= len(possible_starts) <= 2
    if len(possible_starts) == 1:
        # only one choice
        start = possible_starts[0]
    else:
        choice = await current_agent.choose_action_or_square(
            [], possible_starts, "Select a tile.", true_action_hint=None
        )
        start = cast(Square, choice)

    # for bots, choose once
    if not isinstance(current_agent, Human):
        true_action_hint = state.maybe_tile_at(start)
        actions_and_targets = valid_targets(start, state)
        possible_actions = list(actions_and_targets.keys())
        bot_action = await current_agent.choose_action_or_square(
            possible_actions, [], "Select an action.", true_action_hint
        )
        assert isinstance(bot_action, Action)
        target = await current_agent.choose_action_or_square(
            [], actions_and_targets[bot_action], "Select a target.", None
        )
        assert isinstance(target, Square)
        # show both players the proposed action
        await broadcast_selection_changed(
            state.current_player, start, bot_action, target, players
        )
        return start, bot_action, target

    # for humans, choose in a loop
    # to allow changing out choice of start square & action
    chosen_action: Optional[Action] = None
    while True:
        actions_and_targets = valid_targets(start, state)
        possible_actions = list(actions_and_targets.keys())
        possible_targets = actions_and_targets[chosen_action] if chosen_action else []

        # display the partial selection and valid actions/targets to the
        # current player
        await notify_selection_changed(
            state.current_player, start, chosen_action, None, current_agent.websocket
        )

        if not chosen_action and len(possible_starts) == 1:
            possible_squares = []
            prompt = "Select an action."
        elif not chosen_action:
            possible_squares = possible_starts
            prompt = "Select an action, or a different tile."
        elif len(possible_starts) == 1:
            possible_squares = possible_targets
            prompt = "Select a target, or a different action."
        else:
            possible_squares = possible_starts + possible_targets
            prompt = "Select a target, or a different action or tile."

        choice = await current_agent.choose_action_or_square(
            possible_actions, possible_squares, prompt, true_action_hint=None
        )
        if choice in possible_targets:
            # they chose a target
            # we should now have all 3 selected
            assert chosen_action is not None
            target = cast(Square, choice)

            # show both players the proposed action
            await broadcast_selection_changed(
                state.current_player, start, chosen_action, target, players
            )
            return start, chosen_action, target
        elif choice in possible_actions:
            # they chose an action
            # go around again for the target or different action
            chosen_action = cast(Action, choice)
        else:
            # they chose a start square
            # go around again for the action or different start
            assert choice in possible_starts
            start = cast(Square, choice)
            chosen_action = None


async def _lose_tile(
    player_or_square: Player | Square,
    state: State,
    players: dict[Player, Agent],
) -> None:
    """
     - Prompt the player to choose a tile to lose, if applicable
     - choose the tile to replace it, if applicable
     - log the lost tile
     - update state

    If `player_or_square` is a square, the player must lose the tile on that square.
    (E.g. when that tile was hit by an attack.)

    If `player_or_square` is a player, the player chooses one tile on board to lose.
    (E.g. when the player lost a challenge.)
    We allow the player to cancel and retry that choice when they get to the replacement
    tile.
    """

    # select which tile on board is lost
    # in some cases the player gets a choice
    if isinstance(player_or_square, Square):
        # a specific square was lost to an attack, so they get no choice
        try:
            player = state.player_at(player_or_square)
        except ValueError:
            # if a double-attack killed the square and nothing replaced it,
            # it's possible the square is empty
            # in which case nothing happens
            return
        possible_squares = [player_or_square]
    else:
        # they lost a challenge, so they get a choice if they have multiple tiles
        assert player_or_square in Player
        player = player_or_square
        possible_squares = state.positions[player]

    if len(possible_squares) == 0:
        # they have no tiles to lose
        # i.e. their last tile was already killed by action
        return

    if len(possible_squares) > 1 or len(state.tiles_in_hand[player]) > 0:
        # current player will need to choose something, so set a waiting prompt for opponent
        # and send any state updates so far to both players
        await broadcast_state_changed(state, players)
        await send_prompt(
            "Waiting for opponent to lose tile.",
            players[other_player(player)].websocket,
        )

    agent = players[player]

    if len(possible_squares) > 1:
        choice = await agent.choose_square_or_hand(
            possible_squares,
            [],
            "Choose which tile to lose.",
        )
        square = cast(Square, choice)
    else:
        square = possible_squares[0]

    # choose replacement tile from hand in a loop
    # to enable choosing a different square to lose
    while True:
        # mark the selected tile with an X for this player
        await notify_selection_changed(
            player, start=None, action=None, target=square, websocket=agent.websocket
        )

        tile = state.tile_at(square)
        hand_tiles = state.tiles_in_hand[player]

        if len(hand_tiles) == 0:
            # the player has no tiles in hand, so no choice
            replacement = None
            break

        if len(hand_tiles) == 1:
            # the player only has one tile in hand, so no choice
            replacement = hand_tiles[0]
            break

        if len(possible_squares) == 1:
            # the player chooses the replacement tile
            choice = await agent.choose_square_or_hand(
                possible_squares=[],
                possible_hand_tiles=hand_tiles,
                prompt="Choose the replacement tile from your hand.",
            )
            replacement = cast(Tile, choice)
            break

        # otherwise, the player chooses the replacement tile or changes the lost tile
        choice = await agent.choose_square_or_hand(
            possible_squares=possible_squares,
            possible_hand_tiles=hand_tiles,
            prompt="Choose the replacement tile from your hand, or a different tile to lose.",
        )
        if choice in hand_tiles:
            replacement = cast(Tile, choice)
            break
        else:
            # they changed the lost tile
            # go around the loop again to choose the replacement
            assert choice in possible_squares
            square = cast(Square, choice)
            continue

    # move the tile from alive to dead
    position_index = state.positions[player].index(square)
    state.tiles_on_board[player].pop(position_index)
    state.positions[player].pop(position_index)
    state.tiles_on_board_revealed[player].pop(position_index)
    state.discard.append(tile)

    # move the replacement tile if applicable
    if replacement:
        state.tiles_in_hand[player].remove(replacement)
        state.tiles_on_board[player].append(replacement)
        state.positions[player].append(square)
        state.tiles_on_board_revealed[player].append(False)
        state.log(
            f"{player.format_for_log()} lost {tile} on {square.format_for_log()} and replaced it from hand."
        )
    else:
        state.log(
            f"{player.format_for_log()} lost {tile} on {square.format_for_log()}."
        )

    state.score_point(other_player(player))
    await clear_selection(players)
    await broadcast_state_changed(state, players)


async def _select_response(
    start: Square,
    action: Action,
    target: Square,
    state: State,
    players: dict[Player, Agent],
) -> Response | Tile:
    assert action in Tile

    player_at_target = state.maybe_player_at(target)
    tile_at_target = state.maybe_tile_at(target)

    possible_responses: list[Response | Tile] = [
        Response.ACCEPT,
        Response.CHALLENGE,
    ]
    if action == Tile.HOOK:
        # Tile.HOOK reflects Tile.HOOK
        possible_responses.append(Tile.HOOK)
    elif action == Tile.THIEF:
        # Tile.THIEF reflects Tile.THIEF
        possible_responses.append(Tile.THIEF)
    elif action == Tile.KNIVES:
        # Tile.KNIVES reflects Tile.KNIVES
        possible_responses.append(Tile.KNIVES)
    elif action == Tile.BACKSTABBER:
        # Tile.BACKSTABBER reflects Tile.BACKSTABBER
        possible_responses.append(Tile.BACKSTABBER)
    elif action == Tile.FIREBALL and player_at_target == state.other_player:
        # Tile.FIREBALL reflects Tile.FIREBALL, but only if the direct target is an enemy
        possible_responses.append(Tile.FIREBALL)

    await send_prompt(
        "Waiting for opponent to respond.", players[state.current_player].websocket
    )

    return await players[state.other_player].choose_response(
        possible_responses,
        f"Opponent claimed {action}.  Choose your response.",
        true_response_hint=tile_at_target,
    )


async def _select_reflect_response(
    action: Action, state: State, players: dict[Player, Agent]
) -> Response:
    await send_prompt(
        "Waiting for opponent to respond to reflect.",
        players[state.other_player].websocket,
    )
    response = await players[state.current_player].choose_response(
        [Response.ACCEPT, Response.CHALLENGE],
        f"Opponent reflected with {action}.  Choose your response.",
        true_response_hint=None,
    )
    return cast(Response, response)


async def _select_smite_target(
    state: State, player: Player, players: dict[Player, Agent]
) -> Square:
    await send_prompt(
        "Waiting for opponent to select a tile to smite ⚡",
        players[other_player(player)].websocket,
    )
    choice = await players[player].choose_action_or_square(
        [],
        state.positions[other_player(player)],
        "Select a tile to smite ⚡",
        true_action_hint=None,
    )
    return cast(Square, choice)


async def _maybe_smite(state: State, players: dict[Player, Agent]) -> None:
    """
    Check if either player has enough coins to smite.
    If so, select a target and resolve the smite.
    """
    if state.game_result() != GameResult.ONGOING:
        # sometimes we hit enough coins to smite at the same time as the game ends, if e.g.
        # the opponent lost a challenge.
        # only smite if the game is still ongoing
        return

    # if the current player has enough coins to smite, select a target and resolve the smite
    if state.smite_cost <= state.coins[state.current_player]:
        # the current player must have just gained enough coins to smite
        await clear_selection(players)
        # make sure both players see the updated coin amount before selecting a target
        await broadcast_state_changed(state, players)

        target = await _select_smite_target(state, state.current_player, players)
        await _resolve_smite(state, state.current_player, players, target)

    if state.smite_cost <= state.coins[state.other_player]:
        # the other player must have just gained enough coins to smite
        await clear_selection(players)
        # make sure both players see the updated coin amount before selecting a target
        await broadcast_state_changed(state, players)

        target = await _select_smite_target(state, state.other_player, players)
        await _resolve_smite(state, state.other_player, players, target)


async def _play_one_turn(state: State, players: dict[Player, Agent]) -> None:
    """
    Play one turn, prompting both players for choices as needed.

    Updates `state` with the result of the turn. Doesn't transition to the next turn
    or display that state to the players.
    """

    # maybe give a bonus to current player for starting on the bonus square
    await _resolve_bonus(state, players)

    # the bonus may push the current player's coins above the smite cost
    await _maybe_smite(state, players)

    # current player chooses their move
    start, action, target = await _select_action(state, players)
    if not action in Tile:
        assert action in OtherAction
        # the player didn't claim a tile
        # i.e. they moved or smited
        # so no possibility of challenge
        await _resolve_action(start, action, target, state, players)
        return

    # ask opponent to accept, challenge, or reflect as appropriate
    response = await _select_response(start, action, target, state, players)

    if response == Response.ACCEPT:
        # other player allows the action to proceed
        await _resolve_action(start, action, target, state, players)

    elif response == Response.CHALLENGE:
        state.reveal_at(start)
        start_tile = state.tile_at(start)
        msg = f"{state.current_player.format_for_log()} reveals a {start_tile}."
        if action == start_tile:
            # challenge fails
            # original action succeeds
            state.log(
                msg
                + f" Challenge fails!  First the {action} happens, then {state.other_player.format_for_log()} will choose a tile to lose."
            )
            await _resolve_action(start, action, target, state, players)
            await _lose_tile(state.other_player, state, players)
        else:
            # challenge succeeds
            # original action fails
            state.log(msg + " Challenge succeeds!")
            await clear_selection(players)
            await _lose_tile(state.current_player, state, players)
    else:
        assert action == response
        # the response was to reflect
        # which the original player may challenge
        reflect_response = await _select_reflect_response(response, state, players)
        target_tile = state.tile_at(target)
        reveal_msg = f"{state.other_player.format_for_log()} reveals a {target_tile}."

        if reflect_response == Response.ACCEPT:
            # reflect succeeds
            # original action fails
            state.log(f"{action} reflected.")
            await clear_selection(players)
            await _resolve_action(start, action, target, state, players, reflect=True)
        elif target_tile == response:
            # challenge fails
            # reflect succeeds
            # original action fails
            state.reveal_at(target)
            state.log(
                reveal_msg
                + f" Challenge fails!  First the {response} is reflected, then {state.current_player.format_for_log()} will choose a tile to lose."
            )
            await clear_selection(players)
            await _resolve_action(start, action, target, state, players, reflect=True)
            await _lose_tile(state.current_player, state, players)
        else:
            state.reveal_at(target)
            # challenge succeeds
            # reflect fails
            # original action succeeds
            state.log(
                reveal_msg
                + f" Challenge succeeds!  First the {action} happens, then {state.other_player.format_for_log()} will choose a tile to lose."
            )
            await _resolve_action(start, action, target, state, players)
            await _lose_tile(state.other_player, state, players)

    # the action may push the current player's coins above the smite cost
    # or the opponent's, if an action was reflected
    await _maybe_smite(state, players)


async def play_one_game(
    match_score: dict[Player, int], players: dict[Player, Agent], randomize: bool
) -> dict[Player, int]:
    """
    Play one game on the connected websockets.

    Returns the game score.
    """
    # initialize a new game
    state = new_state(match_score, randomize)
    state.log("New game!")
    await broadcast_state_changed(state, players)

    while state.game_result() == GameResult.ONGOING:
        state.check_consistency()

        await _play_one_turn(state, players)

        state.next_turn()

        await broadcast_state_changed(state, players)

    state.log(f"Game over!  {state.game_result()}!")
    await broadcast_state_changed(state, players)
    return state.game_score


async def play_one_match(players: dict[Player, Agent], randomize: bool) -> None:
    """
    Play games forever in a loop, updating the match score and broadcasting each game's score.

    If randomize is True, all the game start configuration is randomized; otherwise we use
    the default configuration.
    """
    print(f"New match with {players}")
    match_score = {Player.N: 0, Player.S: 0}
    try:
        while True:
            game_score = await play_one_game(match_score.copy(), players, randomize)
            for player, points in game_score.items():
                match_score[player] += points

            await asyncio.sleep(0.5)

            await broadcast_game_over(players, game_score)
    finally:
        for agent in players.values():
            if isinstance(agent, Human):
                await agent.websocket.close()
