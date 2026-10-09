"use strict";

import {HIGHLIGHT} from "./constants.js";


function highlightSquares(squares, board, mySide) {
  // highlight some squares on the board
  // pass an empty list to clear all highlighting
  //
  // a highlighted square holding your own piece is a choice of that piece, which is
  // drawn on the piece rather than the square
  for (const element of board.querySelectorAll(".cell")) {
    // default unhighlighted
    element.classList.remove(HIGHLIGHT, "own-piece");
    if (mySide && element.classList.contains(mySide)) {
      element.classList.add("own-piece");
    }

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

function highlightHand(handTiles, container) {
  // highlight tiles in hand
  // pass an empty list to clear highlighting
  for (const element of container.querySelectorAll('.hand-tile')) {
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

export {highlightSquares, highlightHand, highlightBoardTiles};