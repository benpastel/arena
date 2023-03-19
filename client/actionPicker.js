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

    // index into tile positions & actionTargets of the selected tile
    tile = null;

    // name of the action the selected action
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
        // called when someone clicks on a tile at [row, col]
        //
        // first check whether it's appropriate to interpret this click as
        // choosing a tile.
        //
        // we can choose a tile in CHOOSE_TILE state of course,
        // but also in CHOOSE_ACTION / CHOOSE_TARGET
        // in which case it cancels the previously selected tile and/or action
        if (! ([CHOOSE_TILE, CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state))) {
            console.log(`Ignored click at ${[row, col]} in ${this.state}`);
            return;
        }

        // find the index in positions, if there is one
        for (let t = 0; t < this.positions.length; t++) {
            const [r, c] = this.positions[t];
            if (r === row && c === col) {
                return startChooseAction(t);
            }
        }
        console.log(`Ignored click at ${[row, col]}; tile positions are ${this.positions}`);
    }

    #startChooseAction(tile_index) {
        if (! ([CHOOSE_TILE, CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state))) {
            console.log(`Bad call to startChooseAction from ${this.state}`);
            return;
        }
        this.state = CHOOSE_ACTION;
        this.tile = tile_index;
        this.chosenAction = null;
        this.prompt.innerHTML = "Select an action for that tile.";

        // TODO: set classes to tag action buttons as valid / invalid?
        // TODO: set hover behavior on ALL action buttons?
    }

    tryChooseAction(action) {
        if (! ([CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state))) {
            console.log(`Ignored click on ${action} in ${this.state}`);
            return;
        }

    }

    #startChooseTarget(action) {
        if (! ([CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state))) {
            console.log(`Bad call to startChooseTarget from ${this.state}`);
            return;
        }
        this.state = CHOOSE_TARGET;
        this.chosenAction = action;
        this.prompt.innerHTML = "Select a target for that action.";

        // TODO:
    }

    tryChooseTarget(action) {
        // TODO
    }
}

export { ActionPicker };
