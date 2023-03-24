"use strict";

import {
  ACTIONS
} from "./renderGameState.js";

const INVALID = "invalid";
const VALID = "valid";

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
  for (const element of actionPanel.querySelectorAll("div")) {
    element.classList.remove(VALID, INVALID);

    if (element.dataset.actionName in actionTargets) {
      element.classList.add(VALID);
    } else {
      element.classList.add(INVALID);
    }
  }
}

export { renderPrompt, highlightActions, NEXT_CHOICE_START };