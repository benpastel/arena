"use strict";

import {
  NORTH_PLAYER,
  SOUTH_PLAYER,
  CHOSEN_START,
  CHOSEN_ACTION,
  CHOSEN_TARGET,
} from "./constants.js";

import {findCell} from "./renderState.js";


function markChosenStart(board, start, player) {
  for (const element of board.querySelectorAll(".cell")) {
    element.classList.remove(CHOSEN_START);
    element.classList.remove(`start-${NORTH_PLAYER}`);
    element.classList.remove(`start-${SOUTH_PLAYER}`);
  }
  if (!start) {
    return;
  }
  const [row, col] = start;
  const element = findCell(board, row, col);
  element.classList.add(CHOSEN_START);
  element.classList.add(`start-${player}`);
}

function markChosenAction(actionPanel, actionName) {
  for (const element of actionPanel.querySelectorAll("div")) {
    element.classList.remove(CHOSEN_ACTION);
  }
  if (!actionName) {
    return;
  }
  for (const element of actionPanel.querySelectorAll("div")) {
    if (element.dataset.name === actionName) {
      element.classList.add(CHOSEN_ACTION);
    }
  }
}

function markChosenTarget(board, target, player) {
  for (const element of board.querySelectorAll(".cell")) {
    element.classList.remove(CHOSEN_TARGET);
    element.classList.remove(`target-${NORTH_PLAYER}`);
    element.classList.remove(`target-${SOUTH_PLAYER}`);
  }
  if (!target) {
    return;
  }
  const [row, col] = target;
  const element = findCell(board, row, col);
  element.classList.add(CHOSEN_TARGET);
  element.classList.add(`target-${player}`);
}

export {markChosenStart, markChosenAction, markChosenTarget};