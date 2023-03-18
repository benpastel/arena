"use strict";

// Selecting an action is a state machine:
//
//        +   <----     send move to server      <---  +
//        ↓                                            ↑
// (waitForTurn) -> chooseTile -> chooseAction -> chooseTarget
//                      ↑              ↓
//                      + <- cancel <- +
const STATE = [
    "waitForTurn",
    "chooseTile",
    "chooseAction",
    "chooseTarget",
];

function waitForTurn(prompt) {
    prompt.innerHTML = "Waiting for opponent to play.";
}

function chooseTile(prompt) {
    prompt.innerHTML = "Your turn!  Select a tile on the board.";
}

function chooseAction(prompt) {
    prompt.innerHTML = "Select an action for that tile.";
}

function chooseTarget(prompt) {
    prompt.innerHTML = "Select a target for that action.";
}

export { waitForTurn, chooseTile, chooseAction, chooseTarget };
