"use strict";

// Draws the choices of a turn on the board.
//
//  - Once a piece is picked, every square it can reach shows a small glyph for each
//    ability that can target it; clicking one picks the ability and the target at once.
//  - A finished claim is a line from the piece to its target in the claimant's colour,
//    annotated with the claimed ability.  A reflect is added to the note, and so are
//    the responses (✓, 🚩, reflect) when it's this player's turn to respond.
//  - A target picked on its own (the tile a player is about to lose) is a pick.

import {
  CHOSEN_START,
  CHOSEN_TARGET,
  ACTION_NAMES,
  RESPONSES,
  ALL_TILES,
  TILES,
} from "./constants.js";

import {findCell} from "./renderState.js";

const SVG = "http://www.w3.org/2000/svg";

// how far the claim's note sits off its line, as a fraction of the board's width
const NOTE_OFFSET = 0.025;


function pieceCenter(board, square) {
  const [row, col] = square;
  const cell = findCell(board, row, col).getBoundingClientRect();
  const origin = board.getBoundingClientRect();
  return [cell.left + cell.width / 2 - origin.left, cell.top + cell.height / 2 - origin.top];
}

function option(name) {
  // a clickable glyph for an ability or a response; tiles are their own glyph, and
  // the rest (↕ ⚡ ✓ 🚩) sit in a shell drawn to match a tile's frame
  const element = document.createElement("span");
  element.classList.add("option");
  element.dataset.name = name;
  element.title = ACTION_NAMES[name];
  if (!(name in TILES)) {
    element.classList.add("shell");
    const symbol = document.createElement("span");
    symbol.classList.add("symbol");
    const text = document.createElement("span");
    text.textContent = name;
    symbol.append(text);
    element.append(symbol);
  } else {
    element.textContent = name;
  }
  return element;
}

// options in a square are always in the same order: the tiles as listed, then ↕ last
const TILE_ORDER = ALL_TILES.map(([tile]) => tile);
function optionOrder(action) {
  const index = TILE_ORDER.indexOf(action);
  return index === -1 ? TILE_ORDER.length : index;
}

function drawTargets(board, targets) {
  const bySquare = new Map();
  for (const [action, squares] of Object.entries(targets)) {
    for (const [row, col] of squares) {
      const key = `${row},${col}`;
      if (!bySquare.has(key)) {
        bySquare.set(key, {row, col, actions: []});
      }
      bySquare.get(key).actions.push(action);
    }
  }
  for (const {row, col, actions} of bySquare.values()) {
    const options = document.createElement("div");
    options.classList.add("cell-options");
    actions.sort((a, b) => optionOrder(a) - optionOrder(b));
    for (const action of actions) {
      options.append(option(action));
    }
    findCell(board, row, col).append(options);
  }
}

function drawClaim(board, selection, responses) {
  const {player, start, action, target, reflect} = selection;
  const [x1, y1] = pieceCenter(board, start);
  const [x2, y2] = pieceCenter(board, target);
  const width = board.getBoundingClientRect().width;

  // the note sits beside the middle of the line, on its upper (or right) side, running
  // away from the line; with no line (a claim on its own square) it sits above the piece
  let noteX = (x1 + x2) / 2;
  let noteY = (y1 + y2) / 2;
  let anchor = "above";
  const length = Math.hypot(x2 - x1, y2 - y1);
  if (length > 0) {
    const svg = document.createElementNS(SVG, "svg");
    svg.classList.add("claim-line", player);
    // the end says what the claim does there: an arrowhead where the piece moves to,
    // a cross where it attacks
    const [ux, uy] = [(x2 - x1) / length, (y2 - y1) / length];
    const attack = isAttack(board, selection);
    const head = width * 0.04;
    const line = document.createElementNS(SVG, "line");
    line.setAttribute("x1", x1);
    line.setAttribute("y1", y1);
    line.setAttribute("x2", attack ? x2 : x2 - ux * head * 0.8);
    line.setAttribute("y2", attack ? y2 : y2 - uy * head * 0.8);
    svg.append(line);
    if (attack) {
      const arm = width * 0.03;
      for (const halo of [true, false]) {
        for (const [dx, dy] of [[arm, arm], [arm, -arm]]) {
          const stroke = document.createElementNS(SVG, "line");
          stroke.setAttribute("x1", x2 - dx);
          stroke.setAttribute("y1", y2 - dy);
          stroke.setAttribute("x2", x2 + dx);
          stroke.setAttribute("y2", y2 + dy);
          stroke.classList.add(halo ? "claim-halo" : "claim-cross");
          svg.append(stroke);
        }
      }
    } else {
      const arrow = document.createElementNS(SVG, "polygon");
      const [bx, by] = [x2 - ux * head, y2 - uy * head];
      const [px, py] = [-uy * head * 0.55, ux * head * 0.55];
      arrow.setAttribute("points", `${x2},${y2} ${bx + px},${by + py} ${bx - px},${by - py}`);
      svg.append(arrow);
    }
    board.append(svg);

    let [nx, ny] = [-(y2 - y1) / length, (x2 - x1) / length];
    if (ny > 0 || (ny === 0 && nx < 0)) {
      [nx, ny] = [-nx, -ny];
    }
    noteX += nx * width * NOTE_OFFSET;
    noteY += ny * width * NOTE_OFFSET;
    if (Math.abs(nx) > 2 * Math.abs(ny)) {
      anchor = nx > 0 ? "right" : "left";
    } else if (Math.abs(nx) * 2 > Math.abs(ny)) {
      // beside a slanted line, the note hangs from its corner so it stays clear of it
      anchor = nx > 0 ? "above-right" : "above-left";
    }
  } else {
    noteY -= width * 0.08;
  }

  const note = document.createElement("div");
  note.classList.add("claim-note", anchor);
  note.style.left = `${noteX}px`;
  note.style.top = `${noteY}px`;

  const claimed = document.createElement("span");
  claimed.classList.add("claimed", player);
  claimed.textContent = action;
  claimed.title = ACTION_NAMES[action];
  note.append(claimed);

  if (reflect) {
    const reflected = document.createElement("span");
    reflected.classList.add("claimed", player === "north" ? "south" : "north");
    reflected.textContent = reflect;
    reflected.title = ACTION_NAMES[reflect];
    note.append(reflected);
  }

  if (responses.length > 0) {
    // the claim, then a break, then the answers to it
    const separator = document.createElement("span");
    separator.classList.add("note-separator");
    separator.textContent = "—";
    note.append(separator);
  }
  for (const response of responses) {
    note.append(option(response));
  }
  board.append(note);
  keepOnBoard(board, note, noteX, noteY, x1, y1, x2, y2);
}

// abilities whose target is something attacked, rather than a square moved to
const ATTACKS = new Set(["🀒", "🀌", "🀙", "🀛", "🀍"]);

function isAttack(board, {player, action, target}) {
  // a backstabber kills an enemy behind it, but otherwise moves
  if (action === "🀇") {
    const [row, col] = target;
    const enemy = player === "north" ? "south" : "north";
    return findCell(board, row, col).classList.contains(enemy);
  }
  return ATTACKS.has(action);
}

function keepOnBoard(board, note, noteX, noteY, x1, y1, x2, y2) {
  // a note that would run off the board goes on the other side of its line instead
  const bounds = board.getBoundingClientRect();
  const rect = note.getBoundingClientRect();
  const flips = {
    right: "left", left: "right", above: "below",
    "above-right": "below-left", "above-left": "below-right",
  };
  const off =
    rect.left < bounds.left || rect.right > bounds.right ||
    rect.top < bounds.top || rect.bottom > bounds.bottom;
  const anchor = Object.keys(flips).find((a) => note.classList.contains(a));
  if (!off || !anchor) {
    return;
  }
  // mirror the note's point through the line's middle
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;
  note.classList.replace(anchor, flips[anchor]);
  note.style.left = `${2 * midX - noteX}px`;
  note.style.top = `${anchor === "above" && x1 === x2 && y1 === y2 ? midY + (midY - noteY) : 2 * midY - noteY}px`;
}

function clearSelection(board) {
  for (const element of board.querySelectorAll(`.${CHOSEN_START}, .${CHOSEN_TARGET}`)) {
    element.classList.remove(CHOSEN_START, CHOSEN_TARGET);
  }
  for (const element of board.querySelectorAll(".claim-line, .claim-note, .cell-options")) {
    element.remove();
  }
}

function renderSelection(board, selection, highlight) {
  clearSelection(board);
  const targets = highlight?.targets ?? {};
  const actions = highlight?.actions ?? [];

  if (selection && selection.start && selection.action && selection.target) {
    // a finished claim, with the responses to it if they're ours to make
    const responding = actions.some((name) => name in RESPONSES);
    drawClaim(board, selection, responding ? actions : []);
    return;
  }

  if (selection?.start) {
    const [row, col] = selection.start;
    findCell(board, row, col).classList.add(CHOSEN_START);
  }
  if (selection?.target) {
    const [row, col] = selection.target;
    findCell(board, row, col).classList.add(CHOSEN_TARGET);
  }
  drawTargets(board, targets);
}

export {renderSelection};
