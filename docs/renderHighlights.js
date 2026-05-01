"use strict";

import {HIGHLIGHT} from "./constants.js";
import {findCell} from "./renderState.js";

// Map from "row,col" → preview object {target, path, explosion, landing}.
// Set by renderPreviews on each HIGHLIGHT_CHANGE; consulted by hover handlers
// (attached once at startup in main.js).
let currentPreviews = new Map();


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

function _key(row, col) {
  return `${row},${col}`;
}

function renderPreviews(previews, board) {
  // remove old overlays
  for (const overlay of board.querySelectorAll(".preview")) {
    overlay.remove();
  }
  currentPreviews = new Map();

  if (!previews || previews.length === 0) {
    return;
  }

  // collect the union of every target's path/explosion/landing for the static (faint) layer
  const allPath = new Set();
  const allExplosion = new Set();
  const allLanding = new Set();

  for (const p of previews) {
    const [tr, tc] = p.target;
    currentPreviews.set(_key(tr, tc), p);

    for (const [r, c] of p.path || []) allPath.add(_key(r, c));
    for (const [r, c] of p.explosion || []) allExplosion.add(_key(r, c));
    if (p.landing) allLanding.add(_key(p.landing[0], p.landing[1]));
  }

  // attach overlay divs (one per kind, layered with low opacity).
  // hover handlers brighten by toggling .active.
  for (const cell of board.querySelectorAll(".cell")) {
    const r = parseInt(cell.dataset.row);
    const c = parseInt(cell.dataset.column);
    const key = _key(r, c);
    if (allPath.has(key)) _addOverlay(cell, "preview path");
    if (allExplosion.has(key)) _addOverlay(cell, "preview explosion");
    if (allLanding.has(key)) _addOverlay(cell, "preview landing");
  }
}

function _addOverlay(cell, classes) {
  const div = document.createElement("div");
  div.className = classes;
  cell.appendChild(div);
}

function activatePreviewAt(row, col, board) {
  // brighten this target's specific path/explosion/landing.
  // no-op if no preview at (row, col).
  const preview = currentPreviews.get(_key(row, col));
  if (!preview) return;

  for (const [r, c] of preview.path || []) {
    const overlay = findCell(board, r, c).querySelector(".preview.path");
    if (overlay) overlay.classList.add("active");
  }
  for (const [r, c] of preview.explosion || []) {
    const overlay = findCell(board, r, c).querySelector(".preview.explosion");
    if (overlay) overlay.classList.add("active");
  }
  if (preview.landing) {
    const [r, c] = preview.landing;
    const overlay = findCell(board, r, c).querySelector(".preview.landing");
    if (overlay) overlay.classList.add("active");
  }
}

function deactivateAllPreviews(board) {
  for (const overlay of board.querySelectorAll(".preview.active")) {
    overlay.classList.remove("active");
  }
}

export {
  highlightSquares,
  highlightActions,
  highlightHand,
  highlightBoardTiles,
  renderPreviews,
  activatePreviewAt,
  deactivateAllPreviews,
};