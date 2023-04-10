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
    for (const [targetRow, targetCol] of squares) {
      if ((r === targetRow) && (c === targetCol)) {
        element.classList.add(HIGHLIGHT);
      }
    }
  }
}

function highlightActions(actions, actionPanel) {
  // highlight action or response icons
  // pass an empty list to clear highlighting
  console.log(`start highlightActions, highlight ${actions}`);
  for (const element of actionPanel.querySelectorAll("div")) {
    if (actions.includes(element.dataset.name)) {
      element.classList.add(HIGHLIGHT);
      console.log(`highlight ${element.dataset.name}`);
    } else {
      element.classList.remove(HIGHLIGHT);
      console.log(`skip ${element.dataset.name}`);
    }
  }
}

function highlightHand(handTiles, hand) {
  // highlight tiles in hand
  // pass an empty list to clear highlighting
  for (const element of hand.querySelectorAll('.hand-tile')) {
    if (handTiles.includes(element.dataset.tileName)) {
      hand.classList.add(HIGHLIGHT);
    } else {
      hand.classList.remove(HIGHLIGHT);
    }
  }
}

export {highlightSquares, highlightActions, highlightHand};