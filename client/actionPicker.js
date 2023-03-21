"use strict";

const WAIT = "WAIT_STATE";
const CHOOSE_TILE = "CHOOSE_TILE_STATE";
const CHOOSE_ACTION = "CHOOSE_ACTION_STATE";
const CHOOSE_TARGET = "CHOOSE_TARGET_STATE";

class ActionPicker {
    // Selecting an action is a state machine:
    //
    //                    WAIT
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
    //               we send move to server and go back to WAIT
    //
    state = WAIT;

    // an array containing 1 or 2 squares [row, col]
    // representing the positions of
    positions = null;

    // an array of the valid actions & targets corresponding to each position
    // each element in the array is action name => list of valid target squares
    actionTargets = null;

    // index into tile positions & actionTargets of the selected tile
    chosenTile = null;

    // name of the action the selected action
    chosenAction = null;

    constructor(prompt, submitMoveFn) {
        // `prompt` is the html element telling the player what to do
        // `submitMoveFn` submits (tile, action, target) to the server
        this.prompt = prompt;
        this.submitMoveFn = submitMoveFn;
    }

    beginWait() {
        this.state = WAIT;
        this.chosenTile = null;
        this.chosenAction = null;
        this.positions = null;
        this.actionTargets = null;
        this.prompt.innerHTML = "Waiting for opponent.";
    }

    beginChooseTile(positions, actionTargets) {
        if (this.state !== WAIT) {
            console.log(`Ignored call to beginChooseTile from ${this.state}`);
            return;
        }
        this.state = CHOOSE_TILE;
        this.chosenTile = null;
        this.chosenAction = null;
        this.positions = positions;
        this.actionTargets = actionTargets;
        this.prompt.innerHTML = "Select a tile on the board.";
    }

    #beginChooseAction(tileIndex) {
        if (![CHOOSE_TILE, CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state)) {
            console.log(`Ignored call to beginChooseAction from ${this.state}`);
            return;
        }
        console.log(`Selected ${this.positions[tileIndex]}; now choosing action.`);

        this.state = CHOOSE_ACTION;
        this.chosenTile = tileIndex;
        this.chosenAction = null;
        this.prompt.innerHTML = "Select an action for that tile.";

        // TODO: set classes to tag action buttons as valid / invalid?
        // TODO: set hover behavior on ALL action buttons?
    }


    #beginChooseTarget(action) {
        if (![CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state)) {
            console.log(`Ignored call to beginChooseTarget in ${this.state}`);
            return;
        }
        console.log(`Selected ${action}; now choosing target.`);

        this.state = CHOOSE_TARGET;
        this.chosenAction = action;
        this.prompt.innerHTML = "Select a target for that action.";
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
        if (![CHOOSE_TILE, CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state)) {
            console.log(`Ignored click at ${[row, col]} in ${this.state}`);
            return;
        }

        // find the index in positions, if there is one
        for (let t = 0; t < this.positions.length; t++) {
            const [r, c] = this.positions[t];
            if (r === row && c === col) {
                return this.#beginChooseAction(t);
            }
        }
        console.log(`Ignored click at ${[row, col]}; tile positions are ${this.positions}`);
    }

    tryChooseAction(action) {
        if (![CHOOSE_ACTION, CHOOSE_TARGET].includes(this.state)) {
            console.log(`Ignored click on ${action} in ${this.state}`);
            return;
        }
        const okActions = this.actionTargets[this.chosenTile];
        if (action in okActions) {
            return this.#beginChooseTarget(action);
        }
        console.log(`Ignored ${action}; only ${okActions} are valid.`);
        return;
    }

    tryChooseTarget(targetRow, targetCol) {
        if (CHOOSE_TARGET !== this.state) {
            console.log(`Ignored call to tryChooseTarget in ${this.state}`);
            return;
        }
        const okTargets = this.actionTargets[this.chosenTile][this.chosenAction];
        for (const [r, c] of okTargets) {
            if (targetRow === r && targetCol === c) {
                console.log(`Selected ${[targetRow, targetCol]}; submitting to server.`);

                const start = this.positions[this.chosenTile];
                const target = [targetRow, targetCol];

                this.submitMoveFn(start, this.chosenAction, target);
                return this.beginWait();
            }
        }
        console.log(`Ignored ${[targetRow, targetCol]}; only ${okTargets} are valid.`);
        return;
    }
}

export { ActionPicker };
