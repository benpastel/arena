"use strict";

// Selecting an action is a state machine:
//
//        +   <----     send move to server      <---  +
//        ↓                                            ↑
// (waitForTurn) -> chooseTile -> chooseAction -> chooseTarget
//                      ↑              ↓
//                      + <- cancel <- +
//
const WAIT_FOR_TURN = "waitForTurn";
const CHOOSE_TILE = "chooseTile";
const CHOOSE_ACTION = "chooseAction";
const CHOOSE_TARGET = "chooseTarget";

function waitForTurn(uiState, prompt) {
    uiState.state = WAIT_FOR_TURN;
    uiState.chosenTile = null;
    uiState.chosenAction = null;

    prompt.innerHTML = "Waiting for opponent to play.";
}

function startChooseTile(uiState, prompt) {
    uiState.state = CHOOSE_TILE;
    uiState.chosenTile = null;
    uiState.chosenAction = null;

    prompt.innerHTML = "Select a tile on the board.";

    // TODO set maybeChooseTile onclick as a closure that knows the uiState?
    // I think that's just an inner function here.  and then it can look at uiState
    // which we modify to keep up to date.
    // ... but what about the game state?  maybe that's a field on uiState?
    //  and all of this is inside "context"?
}

function tryChooseTile(uiState, chosenTile, gameState) {
    // TODO my idea was to have these "try" methods that maybe
    // initiate a state change and put them in the onClicks
    //
    // but the problem is how does the button know uiState, gameState, etc?
    // I think main loop needs to know uiState, gameState
}



function startChooseAction(tile, uiState, prompt) {
    uiState.state = CHOOSE_ACTION;
    uiState.chosenTile = tile;
    uiState.chosenAction = null;

    prompt.innerHTML = "Select an action for that tile.";
}

function startChooseTarget(action, uiState, prompt) {
    uiState.state = CHOOSE_ACTION;
    uiState.chosenAction = action;

    prompt.innerHTML = "Select a target for that action.";
}

function finish(target, uiState, prompt) {

    // TODO notify server

    waitForTurn(uiState, prompt);
}

export { waitForTurn };
