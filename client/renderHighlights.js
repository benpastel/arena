"use strict";

import {PLAYERS} from "./renderState.js";

// must match css classes
const HIGHLIGHT_SQUARE = "highlight-square";
const HIGHLIGHT_ACTION = "highlight-action";
const HIGHLIGHT_HAND = "highlight-hand";

function highlightSquares(squares, board) {
  // highlight some squares on the board
  // pass an empty list to clear all highlighting
  for (const element of board.querySelectorAll(".cell")) {
    // default unhighlighted
    element.classList.remove(HIGHLIGHT_SQUARE);

    // highlight if in target list
    const r = parseInt(element.dataset.row);
    const c = parseInt(element.dataset.column);

    // can't use "in" on arrays in javascript, so iterate through targets explicitly
    for (const [targetRow, targetCol] of targets) {
      if ((r === targetRow) && (c === targetCol)) {
        element.classList.add(HIGHLIGHT_SQUARE);
      }
    }
  }
}

function highlightActions(actions, actionPanel) {
  // highlight action or response icons
  // pass an empty list to clear all highlighting
  for (const element of actionPanel.querySelectorAll("div")) {
    if (element.dataset.name in actions) {
      element.classList.add(HIGHLIGHT_ACTION);
    } else {
      element.classList.remove(HIGHLIGHT_ACTION);
    }
  }
}

// TODO LEFT OFF HERE:
// - register listener
// - update a bunch of CSS
// - remove actionTargets
// - try it!

function highlightHand(handTiles, hand) {
  // TODO explain
  for (const element of panel.querySelectorAll('.hand-tile')) {
    if (element.dataset.tileName in handTiles) {
      panel.classList.add(HIGHLIGHT_HAND);
    } else {
      panel.classList.remove(HIGHLIGHT_HAND);
    }
  }
}

export {highlightSquares, highlightActions, highlightHand};