"use strict";

// A choice that isn't of a square is offered in a panel beside the square it's about,
// pointing at it, on whichever side it fits:
//
//  - the answers to a claim (✓, 🚩, reflect), beside the claim's target, or beside the
//    claimant when answering a reflect, on the side away from the claim's line
//  - an exchange: your tile, then the exchange's two, beside the exchange
//  - a replacement: your hand, beside the empty place it fills
//
// Each tile or answer in the panel carries what clicking it sends.

import {RESPONSES} from "./constants.js";
import {findCell} from "./renderState.js";
import {option} from "./renderSelection.js";

// the sides a panel can sit on, as the direction from its square
const SIDES = {above: [0, -1], below: [0, 1], right: [1, 0], left: [-1, 0]};

// what the choice is, its square, and the side of the square it would rather sit on
function choiceOf(board, selection, highlight, me) {
  if (!highlight || !me) {
    return null;
  }
  const actions = highlight.actions ?? [];
  if (selection?.start && selection.target && actions.some((name) => name in RESPONSES)) {
    const [anchor, away] = selection.reflect
      ? [selection.start, selection.target]
      : [selection.target, selection.start];
    return {
      cell: findCell(board, ...anchor),
      items: actions.map((name) => ({pick: "button", name})),
      // away from the line, then across it, then along it
      sides: byDirection(anchor, away),
    };
  }
  const boardTiles = highlight.boardTiles ?? [];
  if (boardTiles.length > 0) {
    // ours is the last; the exchange we stand on is the one with ours on it
    const ours = boardTiles[boardTiles.length - 1];
    const cells = [...board.querySelectorAll(`.cell.exchange.${me}`)];
    const cell =
      cells.find((c) => c.querySelector(".piece")?.dataset.tileName === ours) ?? cells[0];
    if (!cell) {
      return null;
    }
    return {
      cell,
      items: [
        {pick: "boardTile", name: ours, mine: true},
        ...boardTiles.slice(0, -1).map((name, i) => ({pick: "boardTile", name, apart: i === 0})),
      ],
      sides: ["above", "below", "right", "left"],
    };
  }
  const handTiles = highlight.handTiles ?? [];
  if (handTiles.length > 0) {
    const cell = board.querySelector(`.vacancy.${me}`)?.closest(".cell");
    if (!cell) {
      return null;
    }
    return {
      cell,
      items: handTiles.map((name) => ({pick: "handTile", name, mine: true})),
      sides: ["above", "below", "right", "left"],
    };
  }
  return null;
}

// the sides of `square`, least toward `other` first; on the board, rows run down
function byDirection([row, col], [otherRow, otherCol]) {
  const [dx, dy] = [otherCol - col, otherRow - row];
  return Object.keys(SIDES).sort((a, b) => {
    const [ax, ay] = SIDES[a];
    const [bx, by] = SIDES[b];
    return ax * dx + ay * dy - (bx * dx + by * dy);
  });
}

// put the panel on the first of `sides` where it fits on the board, else where there's
// most room, and point it at the square
function place(board, panel, cell, sides) {
  // all inside the board's border, where the panel is positioned
  const outer = board.getBoundingClientRect();
  const bounds = {width: board.clientWidth, height: board.clientHeight};
  const square = cell.getBoundingClientRect();
  const [width, height] = [panel.offsetWidth, panel.offsetHeight];
  const gap = bounds.width * 0.02;
  const [x, y] = [
    square.left - outer.left - board.clientLeft,
    square.top - outer.top - board.clientTop,
  ];
  const centre = [x + square.width / 2, y + square.height / 2];
  const spots = {
    above: [centre[0] - width / 2, y - gap - height],
    below: [centre[0] - width / 2, y + square.height + gap],
    right: [x + square.width + gap, centre[1] - height / 2],
    left: [x - gap - width, centre[1] - height / 2],
  };
  // how far the panel would run off the board on its side
  const over = (side) => {
    const [left, top] = spots[side];
    return Math.max(0, -left, -top, left + width - bounds.width, top + height - bounds.height);
  };
  const across = (side) => (side === "above" || side === "below" ? 0 : 1);
  const fits = (side) => {
    // sliding along its side is fine; only running off past the square's side isn't
    const [left, top] = spots[side];
    return across(side) === 0
      ? top >= 0 && top + height <= bounds.height
      : left >= 0 && left + width <= bounds.width;
  };
  const side = sides.find(fits) ?? [...sides].sort((a, b) => over(a) - over(b))[0];
  const clamp = (value, size, room) => Math.min(Math.max(value, 0), Math.max(0, room - size));
  const left = clamp(spots[side][0], width, bounds.width);
  const top = clamp(spots[side][1], height, bounds.height);
  panel.classList.add(side);
  panel.style.left = `${left}px`;
  panel.style.top = `${top}px`;
  // the pointer, along the panel's edge, as near the square's middle as it can be
  const point = across(side) === 0 ? centre[0] - left : centre[1] - top;
  const length = across(side) === 0 ? width : height;
  panel.style.setProperty("--point", `${Math.min(Math.max(point, 14), length - 14)}px`);
}

function renderChoice(board, selection, highlight, me) {
  board.querySelector(".choice-panel")?.remove();
  const choice = choiceOf(board, selection, highlight, me);
  if (!choice) {
    return;
  }
  const panel = document.createElement("div");
  panel.className = "choice-panel";
  for (const {pick, name, mine, apart} of choice.items) {
    const item = option(name);
    item.dataset.pick = pick;
    item.classList.toggle("mine", Boolean(mine));
    item.classList.toggle("apart", Boolean(apart));
    panel.append(item);
  }
  board.append(panel);
  place(board, panel, choice.cell, choice.sides);
}

export {renderChoice};
