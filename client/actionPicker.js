"use strict";

const WAIT_FOR_TURN = "waitForTurn";
const CHOOSE_TILE = "chooseTile";
const CHOOSE_ACTION = "chooseAction";
const CHOOSE_TARGET = "chooseTarget";

class ActionPicker {
    // Selecting an action is a state machine:
    //
    //                 WAIT_FOR_TURN  ->  ->
    //                      ↓
    //                      ↓ server says it's our turn
    //                      ↓
    //                 CHOOSE_TILE
    //                      ↓
    //                      ↓ player clicks on one of their tiles
    //                      ↓
    //            + -> CHOOSE_ACTION ⥀ (player clicks on the other tile)
    //   player   ↑         ↓
    //  clicks on ↑         ↓
    //  different ↑         ↓ player clicks on one of their actions
    //     tile   ↑         ↓
    //            + <- CHOOSE_TARGET ⥀ (player clicks on another action)
    //                      ↓
    //               player clicks on a valid target
    //               we send move to server and go back to WAIT_FOR_TURN
    //
    state = WAIT_FOR_TURN;

    // an array containing 1 or 2 squares [row, col]
    // representing the positions of
    positions = null;

    // an array of the valid actions & targets corresponding to each position
    // each element in the array is action name => list of valid target squares
    actionTargets = null;

    // the tile the player has selected so far
    tile = null;

    // the action the player has selected so far
    action = null;

    constructor(prompt) {
        this.prompt = prompt;
    }

    beginWaitForTurn() {
        this.state = WAIT_FOR_TURN;
        this.chosenTile = null;
        this.chosenAction = null;
        this.positions = null;
        this.actionTargets = null;
        this.prompt.innerHTML = "Waiting for opponent to play.";
    }

    beginChooseTile(positions, actionTargets) {
        if (this.state !== WAIT_FOR_TURN) {
            console.log(`Bad call to beginChooseTile from ${this.state}`);
            return;
        }
        this.state = CHOOSE_TILE;
        this.chosenTile = null;
        this.chosenAction = null;
        this.positions = positions;
        this.actionTargets = actionTargets;
        this.prompt.innerHTML = "Select a tile on the board.";
    }

    tryChooseTile(row, col) {
        // attempt to choose a tile
        // this can be in CHOOSE_TILE state
        // or in CHOOSE_ACTION / CHOOSE_TARGET in which case it cancels
        // the previously selected tile or action
        if (! ([CHOOSE_TILE, CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state))) {
            console.log(`Ignored click at ${[row, col]} in ${this.state}`);
            return;
        }

        let chosenTile = null;
        for (let t = 0; t < this.positions.length; t++) {
            const [r, c] = this.positions[t];
            if (r === row && c === col) {
                chosenTile = [r, c];
            }
        }
        if (chosenTile !== null) {
            startChooseAction(chosenTile);
        } else {
            console.log(`Ignored click at ${[row, col]}; tile positions are ${this.positions}`);
        }
    }

    startChooseAction(tile) {
        if (! ([CHOOSE_TILE, CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state))) {
            console.log(`Bad call to startChooseAction from ${this.state}`);
            return;
        }
        this.state = CHOOSE_ACTION;
        this.chosenTile = tile;
        this.chosenAction = null;
        this.prompt.innerHTML = "Select an action for that tile.";
    }

    tryChooseAction(action) {
        // TODO
    }

    startChooseTarget(action) {
        if (! ([CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state))) {
            console.log(`Bad call to startChooseTarget from ${this.state}`);
            return;
        }
        this.state = CHOOSE_TARGET;
        this.chosenAction = action;
        this.prompt.innerHTML = "Select a target for that action.";
    }

    tryChooseTarget(action) {
        // TODO
    }
}

export { ActionPicker };
