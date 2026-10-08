"use strict";

// Shows what's been picked this turn, and the claim on the table.
//
// While a player is still choosing, their picks (the piece, the ability) get a thick
// ring.  A finished claim is drawn for both players instead: a line from the piece
// to its target in the claimant's colour, with the claimed ability's glyph on the
// piece.  A target on its own (the tile a player is about to lose) is a pick.

import {
  CHOSEN_START,
  CHOSEN_ACTION,
  CHOSEN_TARGET,
} from "./constants.js";

import {findCell} from "./renderState.js";

const SVG = "http://www.w3.org/2000/svg";


function cellCenter(board, square) {
  // on a special square the piece sits in the top half, so anchor on the piece
  const [row, col] = square;
  const element = findCell(board, row, col);
  const cell = (element.querySelector(".topRow") || element).getBoundingClientRect();
  const origin = board.getBoundingClientRect();
  return [cell.left + cell.width / 2 - origin.left, cell.top + cell.height / 2 - origin.top];
}

function drawClaimLine(board, start, target, player) {
  const svg = document.createElementNS(SVG, "svg");
  svg.classList.add("claim-line", player);
  const [x1, y1] = cellCenter(board, start);
  const [x2, y2] = cellCenter(board, target);

  const line = document.createElementNS(SVG, "line");
  line.setAttribute("x1", x1);
  line.setAttribute("y1", y1);
  line.setAttribute("x2", x2);
  line.setAttribute("y2", y2);
  svg.append(line);

  const end = document.createElementNS(SVG, "circle");
  end.setAttribute("cx", x2);
  end.setAttribute("cy", y2);
  end.setAttribute("r", Math.min(window.innerWidth, window.innerHeight) * 0.015);
  svg.append(end);

  board.append(svg);
}

function addClaimBadge(board, start, action, player) {
  const [row, col] = start;
  const badge = document.createElement("span");
  badge.classList.add("claim-badge", player);
  badge.textContent = action;
  findCell(board, row, col).append(badge);
}

function clearSelection(board, actionPanel) {
  for (const element of board.querySelectorAll(`.${CHOSEN_START}, .${CHOSEN_TARGET}`)) {
    element.classList.remove(CHOSEN_START, CHOSEN_TARGET);
  }
  for (const element of board.querySelectorAll(".claim-line, .claim-badge")) {
    element.remove();
  }
  for (const element of actionPanel.querySelectorAll(`.${CHOSEN_ACTION}`)) {
    element.classList.remove(CHOSEN_ACTION);
  }
}

function renderSelection(board, actionPanel, selection) {
  clearSelection(board, actionPanel);
  if (!selection) {
    return;
  }
  const {player, start, action, target} = selection;

  if (start && action && target) {
    // a finished claim
    if (start[0] !== target[0] || start[1] !== target[1]) {
      drawClaimLine(board, start, target, player);
    }
    addClaimBadge(board, start, action, player);
    return;
  }

  // picks still being made
  if (start) {
    const [row, col] = start;
    findCell(board, row, col).classList.add(CHOSEN_START);
  }
  if (action) {
    for (const element of actionPanel.querySelectorAll("[data-name]")) {
      if (element.dataset.name === action) {
        element.classList.add(CHOSEN_ACTION);
      }
    }
  }
  if (target) {
    const [row, col] = target;
    findCell(board, row, col).classList.add(CHOSEN_TARGET);
  }
}

export {renderSelection};
