"use strict";

import {
  NORTH_PLAYER,
  SOUTH_PLAYER,
  CHOSEN_START,
  CHOSEN_ACTION,
  CHOSEN_TARGET,
  NORTH_TARGET,
  SOUTH_TARGET,
} from "./constants.js";


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

function markChosenTarget(board, target, player) {
  for (const element of board.querySelectorAll(".cell")) {
    element.classList.remove(CHOSEN_TARGET);
    element.classList.remove(NORTH_TARGET);
    element.classList.remove(SOUTH_TARGET);
  }
  if (!target) {
    return;
  }
  const [targetRow, targetCol] = target;

  let targetPlayerClass = "target-none";
  if (player === NORTH_PLAYER) {
    targetPlayerClass = NORTH_TARGET;
  } else if (player === SOUTH_PLAYER) {
    targetPlayerClass = SOUTH_TARGET;
  }

  for (const element of board.querySelectorAll(".cell")) {
    const r = parseInt(element.dataset.row);
    const c = parseInt(element.dataset.column);
    if ((r === targetRow) && (c === targetCol)) {
      element.classList.add(CHOSEN_TARGET);
      element.classList.add(targetPlayerClass);
    }
  }
}

export {markChosenStart, markChosenAction, markChosenTarget};