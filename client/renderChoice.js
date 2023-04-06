"use strict";

import { ACTIONS } from "./renderState.js";

// must match css
const VALID_ACTION = "valid-action";
const VALID_TARGET = "valid-target";
const CHOSEN_START = "chosen-start";
const CHOSEN_ACTION = "chosen-action";
const CHOSEN_TARGET = "chosen-target";


// TODO abstract the cell stuff
function markChosenStart(board, start) {
  for (const element of board.querySelectorAll(".cell")) {
    element.classList.remove(CHOSEN_START);
  }
  if (!start) {
    return;
  }
  const [targetRow, targetCol] = start;
  for (const element of board.querySelectorAll(".cell")) {
    const r = parseInt(element.dataset.row);
    const c = parseInt(element.dataset.column);
    if ((r === targetRow) && (c === targetCol)) {
      element.classList.add(CHOSEN_START);
    }
  }
}

function markChosenAction(actionPanel, actionName) {
  for (const element of actionPanel.querySelectorAll("div")) {
    if (element.dataset.actionName === actionName) {
      element.classList.add(CHOSEN_ACTION);
    } else {
      element.classList.remove(CHOSEN_ACTION);
    }
  }
}

function markChosenTarget(board, target) {
  for (const element of board.querySelectorAll(".cell")) {
    element.classList.remove(CHOSEN_TARGET);
  }
  if (!target) {
    return;
  }
  const [targetRow, targetCol] = target;
  for (const element of board.querySelectorAll(".cell")) {
    const r = parseInt(element.dataset.row);
    const c = parseInt(element.dataset.column);
    if ((r === targetRow) && (c === targetCol)) {
      element.classList.add(CHOSEN_TARGET);
    }
  }
}

function highlightOkActions(actionPanel, actionTargets) {
  // mark the action divs as valid or invalid choices
  // depending on whether the action is a key in `actionTargets`
  for (const element of actionPanel.querySelectorAll("div")) {
    if (element.dataset.actionName in actionTargets) {
      element.classList.add(VALID_ACTION);
    } else {
      element.classList.remove(VALID_ACTION);
    }
  }
}

function highlightOkTargets(board, targets) {

  // mark board cells as valid or invalid choices for target
  // depending on whether they appear in the target list
  for (const element of board.querySelectorAll(".cell")) {
    // default invalid
    element.classList.remove(VALID_TARGET);

    // valid if in target list
    const r = parseInt(element.dataset.row);
    const c = parseInt(element.dataset.column);

    for (const [targetRow, targetCol] of targets) {
      if ((r === targetRow) && (c === targetCol)) {
        element.classList.add(VALID_TARGET);
      }
    }
  }
}

export { highlightOkActions, highlightOkTargets, markChosenStart, markChosenAction, markChosenTarget };