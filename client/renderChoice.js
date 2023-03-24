"use strict";

import {
  ACTIONS
} from "./renderGameState.js";

// must match css
// TODO: make invalid just the absence of valid
const VALID_ACTION = "valid-action";
const INVALID_ACTION = "invalid-action";
const VALID_TARGET = "valid-target";
const INVALID_TARGET = "invalid-target";

// must match python enum
const NEXT_CHOICE_START = "START";
const NEXT_CHOICE_ACTION = "ACTION";
const NEXT_CHOICE_TARGET = "TARGET";
const NEXT_CHOICE_RESPONSE = "RESPONSE";


function renderPrompt(prompt, nextChoice) {
  switch (nextChoice) {
    case NEXT_CHOICE_START:
      prompt.innerHTML = 'Select the tile that will take action this turn.';
      break;
    case NEXT_CHOICE_ACTION :
      prompt.innerHTML = 'Select the action to take (or select a new tile).';
      break;
    case NEXT_CHOICE_TARGET:
      prompt.innerHTML = 'Select the target square (or select a new tile/action).';
      break;
    case NEXT_CHOICE_RESPONSE:
      prompt.innerHTML = 'Not implemented yet :(';
      break;
    default:
      throw new Error(`Bad nextChoice ${nextChoice}`);
  }
}

function highlightActions(actionPanel, actionTargets) {
  // mark the action divs as valid or invalid choices
  // depending on whether the action is a key in `actionTargets`
  for (const element of actionPanel.querySelectorAll("div")) {
    element.classList.remove(VALID_ACTION, INVALID_ACTION);

    if (element.dataset.actionName in actionTargets) {
      element.classList.add(VALID_ACTION);
    } else {
      element.classList.add(INVALID_ACTION);
    }
  }
}

function highlightTargets(board, targets) {

  // mark board cells as valid or invalid choices for target
  // depending on whether they appear in the target list
  for (const element of board.querySelectorAll(".cell")) {
    // default invalid
    element.classList.remove(VALID_TARGET);
    element.classList.add(INVALID_TARGET);

    // valid if in target list
    const r = parseInt(element.dataset.row);
    const c = parseInt(element.dataset.column);

    for (const [targetRow, targetCol] of targets) {
      if ((r === targetRow) && (c === targetCol)) {
        element.classList.remove(INVALID_TARGET);
        element.classList.add(VALID_TARGET);
      }
    }
  }
}

export { renderPrompt, highlightActions, highlightTargets, NEXT_CHOICE_START };