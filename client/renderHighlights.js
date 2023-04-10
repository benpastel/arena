"use strict";

import {PLAYERS} from "./renderState.js";

// must match css classes
const HIGHLIGHT = "highlight";

function highlightSquares(squares, board) {
  // highlight some squares on the board
  // pass an empty list to clear all highlighting
  for (const element of board.querySelectorAll(".cell")) {
    // default unhighlighted
    element.classList.remove(HIGHLIGHT);

    // highlight if in target list
    const r = parseInt(element.dataset.row);
    const c = parseInt(element.dataset.column);

    // can't use "in" on arrays in javascript, so iterate through targets explicitly
    for (const [targetRow, targetCol] of targets) {
      if ((r === targetRow) && (c === targetCol)) {
        element.classList.add(HIGHLIGHT);
      }
    }
  }
}

function highlightActions(actions, actionPanel) {
  // highlight action or response icons
  // pass an empty list to clear highlighting
  for (const element of actionPanel.querySelectorAll("div")) {
    if (element.dataset.name in actions) {
      element.classList.add(HIGHLIGHT);
    } else {
      element.classList.remove(HIGHLIGHT);
    }
  }
}

function highlightHand(handTiles, hand) {
  // highlight tiles in hand
  // pass an empty list to clear highlighting
  for (const element of panel.querySelectorAll('.hand-tile')) {
    if (element.dataset.tileName in handTiles) {
      panel.classList.add(HIGHLIGHT);
    } else {
      panel.classList.remove(HIGHLIGHT);
    }
  }
}

export {highlightSquares, highlightActions, highlightHand};