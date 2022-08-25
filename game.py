from arena.state import (
    new_state,
    check_consistency,
    check_game_result,
    GameResult,
    Player,
    player_view,
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


def _lose_spell(player: Player, state: State) -> None:
    # Ask the player to choose between wizards & spells if more than one available
    #
    # flip the spell tile face-up
    #
    # if it's this wizard's last spell, kill the wizard
    #
    # log & display everything that happened
    assert False, "TODO"

def _redraw_spell(wizard: Wizard, action: Action, state: State) -> None:
    # return the spell in state
    # draw a new spell at random
    # display & log this for the player who can see it
    assert False, "TODO"



def play_one_game():

    # TODO: I think we'll also want to pass current player around, or get it
    # more easily from state

    state = new_state()

    while check_game_result(state) == GameResult.ONGOING:
        # check which actions are possible for the current wizard
        # they must have
        #  - sufficient mana for the action
        #  - at least one valid target for the action
        ok_actions = [
            a
            for a in affordable_actions(state)
            if valid_targets(state.current_wizard, a, state.wizard_positions)
        ]

        action = None
        target = None
        while action is None or target is None:
            # refresh the UI
            # for debugging right now we display the full state
            # TODO use `player_view`
            display_state(state)

            # wait for the active player to tentatively select an action
            # in the final UI this will be when the player mouses over an action
            action = select_action(state.current_wizard, ok_actions)

            # show possible target squares
            # and confirm or cancel
            # if they cancelled, target is None and we'll continue around the loop
            potential_targets = valid_targets(state.current_wizard, action, state.wizard_positions)
            display_targets(potential_targets)
            target = select_target_or_cancel(potential_targets)

        claimed_spell = spell_for_action(action)

        # reset UI to remove targeting
        # TODO use `player_view`
        display_state(state)

        # show other player the proposed action
        # and challenge or accept
        log_proposed_action(state.current_wizard, action, target, claimed_spell)
        display_proposed_action(state.current_wizard, action, target, claimed_spell)

        # depending on the action, response may be to accept, challenge, or block by claiming
        # a blocking spell
        potential_responses = valid_responses(action, target, state)
        response = choose_response(potential_responses)
        log_response(response)

        if response == Response.ACCEPT:
            action_succeeds = True

        elif response == Response.CHALLENGE:

            if is_challenge_successful(claimed_spell, state):
                action_succeeds = False
                log_challenge_success()
                # RULES: change doc to allow either wizard to lose a spell on challenge success
                _lose_spell(state.current_player())
            else:
                action_succeeds = True
                log_challenge_failure()
                _lose_spell(other_player(state.current_player()))
                _redraw_spell()

        else:
            # the response was to block
            # the original player may challenge
            # TODO: will need to move Response and Actions somewhere shared
            response_to_block = choose_response([Response.ACCEPT, Response.CHALLENGE])

            if response_to_block == Response.ACCEPT:
                log_block_success()
                action_succeeds = False
            else:
                claimed_spell_for_block = (
                    Spell.GRAPPLING_HOOK response == Response.BLOCK_WITH_GRAPPLING_HOOK
                    else Spell.BIRD_KNIGHT
                )
                if is_challenge_successful(claimed_spell_for_block, state):
                    # this player successfully challenged the block, so the original
                    # action succeeds
                    log_challenge_success()
                    _lose_spell(other_player(state.current_player()))
                    action_succeeds = True
                else:
                    # the block succeeds
                    log_challenge_failure()
                    _lose_spell(state.current_player())
                    action_succeeds = False

        # unless successfully challenged, do the action
        # TODO: we need to check action is still valid
        if action_succeeds:
            hit_wizard = resolve_action()
            log_action_result()

            if hit_wizard:
                # TODO this needs to be defined for both wizards and players
                _lose_spell(hit_wizard)

        display_state(state)

        state.rotate_player(state)
        check_consistency(state)

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
