from arena.state import (
    new_state,
    check_consistency,
    check_game_result,
    GameResult,
    Player,
    player_view,
    ACTIONS_TO_SPELLS,
    RESPONSE_TO_SPELL
)
from arena.actions import (
    affordable_actions,
    valid_targets,
    is_challenge_successful,
    resolve_action
)
from arena.display import (
    display_state,
    display_targets,
    display_proposed_action
)

from arena.inputs import (
    select_action,
    select_target_or_cancel,
    challenge_or_accept
)
from arena.logs import (
    log_proposed_action,
    log_challenge_success,
    log_challenge_failure,
    log_action_result
)


def _select_action(state: State) -> Tuple[Action, Square | Wizard]:
    '''
    Prompt the player to choose a valid action & target square for this turn.
    '''

    # check which actions are possible for the current wizard
    # they must have
    #  - sufficient mana for the action
    #  - at least one valid target for the action
    ok_actions = [
        a
        for a in affordable_actions(state)
        if valid_targets(state.current_wizard(), a, state.wizard_positions)
    ]

    # RULES: if no possible actions, the player loses or skips their turn?
    assert ok_actions, "TODO: handle no possible action case"

    action = None
    target_square = None
    while action is None or target is None:
        # wait for the active player to tentatively select an action
        # in the final UI this will be when the player mouses over an action
        action = select_action(state.current_wizard(), ok_actions)

        # show possible target squares
        # and confirm or cancel
        potential_targets = valid_targets(state.current_wizard, action, state.wizard_positions)
        display_targets(potential_targets)
        target_square = select_target_or_cancel(potential_targets)

        # refresh the UI to remove targeting overlay
        display_state(state)

        # if target is None, they cancelled, so try again

    # if the action targeted a wizard, return that wizard
    for wizard, position in wizard_positions.item():
        if position == target_square:
            return action, wizard

    # otherwise return the target coordinates
    return action, target_square

def _lose_spell(wizards: List[Wizard], state: State) -> None:
    '''
    Prompt the player to choose a spell to lose, and log the choice
    '''
    assert wizards

    # flatten options
    options = [
        (wizard, spell, spell_idx)
        for wizard in wizards
        for spell_idx, spell in enumerate(wizard_spells[wizard])
    ]

    if len(options) == 0:
        # these wizards have already lost all their spells; do nothing
        return

    if len(options) == 1:
        # there's no choice
        wizard, spell, spell_idx = options[0]

    else:
        # ask the player
        wizard, spell, spell_idx = select_spell_to_lose(options)

    # move the spell tile from live to dead
    state.wizard_spells[wizard].pop(spell_idx)
    dead_spells[wizard].append(spell)
    log_spell_lost(wizard, spell)

    # if this was the wizard's last spell, the wizard is now KO'd
    if not wizard_spells[wizard]:
        log_wizard_lost(wizard)


def _resolve_action(action: Action, target: Square | Wizard, state: State) -> None:
    # TODO maybe break this into pieces around moving, spending mana, destroying?

    # the action may hit any number of
    hit_wizards = do_action(action, target, state)

    for hit_wizard in hit_wizards:
        _lose_spell(hit_wizard, state)


def _redraw_spell(wizard: Wizard, action: Action, state: State) -> None:
    # return the spell in state
    # draw a new spell at random
    # display & log this for the player who can see it
    assert False, "TODO"


def play_one_game():

    state = new_state()

    # TODO
    _place_spells(state, player.N)
    _place_spells(state, player.S)

    while check_game_result(state) == GameResult.ONGOING:
        display_state(state)
        check_consistency(state)

        player = state.current_player()

        source = _select_source(state)
        action, target = _select_action(source_square, state)
        claimed_spell = ACTIONS_TO_SPELLS.get(action)

        if claimed_spell is None:
            # the player didn't claim a spell
            # i.e. they moved or smited
            # so no possibility of challenge
            log_action(action, target)
            _resolve_action(action, target, state)
            state.turn_count += 1
            continue

        # show other player the proposed action
        # ask whether they accept, challenge, or block
        log_proposed_action(player, source, action, target, claimed_spell)
        display_proposed_action(player, source, action, target, claimed_spell)

        potential_responses = valid_responses(action, target, state)
        response = choose_response(potential_responses)
        log_response(response)

        if response == Response.ACCEPT:
            _resolve_action(source, action, target, state)

        elif response == Response.CHALLENGE:
            if claimed_spell == state.square_to_spell()[source]:
                # the challenge fails
                # the original action succeeds
                log_challenge_failure()
                _lose_spell(state.other_player(), state)
                _resolve_action(action, target, state)
            else:
                # the challenge succeeds
                # the original action fails
                log_challenge_success()
                _lose_spell(state.current_player(), state)

        else:
            # the response was to block
            # blocking means the target is claiming a spell
            # which the original player may challenge
            target_claimed_spell = RESPONSE_TO_SPELL[response]
            log_proposed_block(target, target_claimed_spell)
            response_to_block = choose_response([Response.ACCEPT, Response.CHALLENGE])

            if response_to_block == Response.ACCEPT:
                log_block_success()
                # TODO: blocking Grappling Hook as Grappling Hook will steal 1 from the source

            elif target_claimed_spell == state.square_to_spell()[target]:
                # the challenge fails
                # the block succeeds
                # the original action fails
                # TODO: blocking Grappling Hook as Grappling Hook will steal 1 from the source
                log_challenge_failure(target, target_claimed_spell)
                _lose_spell(state.current_player(), state)
            else:
                # the challenge succeeds
                # the block fails
                # the original action succeeds
                log_challenge_success(target, target_claimed_spell)
                _lose_spell(state.other_player(), state)
                _resolve_action(source, action, target, state)

        state.turn_count += 1

    display_state(state)
    log_game_end()

    # later: prompt for a new game with starting player rotated
    # also keep a running total score for longer matches


def show_start_views():
    ''' Start a new game and show both players' views, for debugging. '''
    state = new_state()
    check_consistency(state)
    assert check_game_result(state) == GameResult.ONGOING

    print("Private server state:")
    display_state(state)

    print("\n\n\nNorth's view:")
    display_state(player_view(state, Player.N))

    print("\n\n\nSouth's view:")
    display_state(player_view(state, Player.S))


if __name__ == "__main__":
    play_one_game()
