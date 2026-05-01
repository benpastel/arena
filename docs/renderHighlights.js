"use strict";

import {HIGHLIGHT} from "./constants.js";


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
  for (const element of actionPanel.querySelectorAll("div")) {
    if (actions.includes(element.dataset.name)) {
      element.classList.add(HIGHLIGHT);
    } else {
      element.classList.remove(HIGHLIGHT);
    }
  }
}

function highlightHand(handTiles, infoPanel) {
  // highlight tiles in hand
  // pass an empty list to clear highlighting
  for (const element of infoPanel.querySelectorAll('.hand-tile')) {
    if (handTiles.includes(element.dataset.tileName)) {
      element.classList.add(HIGHLIGHT);
    } else {
      element.classList.remove(HIGHLIGHT);
    }
  }
}

function highlightBoardTiles(boardTiles, board) {
  // highlight tiles on board
  // pass an empty list to clear highlighting
  for (const element of board.querySelectorAll('.board-tile')) {
    if (boardTiles.includes(element.dataset.tileName)) {
      element.classList.add(HIGHLIGHT);
    } else {
      element.classList.remove(HIGHLIGHT);
    }
  }
}

export {highlightSquares, highlightActions, highlightHand, highlightBoardTiles};