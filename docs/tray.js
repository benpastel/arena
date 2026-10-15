"use strict";

// The tray: every tile in the game, three copies of each kind in play, a row to a kind,
// each copy drawn with what we know of it:
//   - ours, in our colour, and theirs once we've seen it, in theirs
//   - dead, in the colour of whoever it was, with a tombstone in its corner
//   - unused, seen with the bonus, with a magnifying glass in its corner
//   - unknown, pale
//
// Our copies start on the left. After that a copy keeps its place as what we know of
// it changes (ours dies where it was), and a copy we newly know of takes a row's
// leftmost unknown place, so nothing is ever reordered.

import {HIDDEN_TILE, ACTION_NAMES} from "./constants.js";

const COPIES = 3;
// what a copy can be, in the order newly known copies fill a row's free places
const KINDS = ["you", "them", "you-dead", "them-dead", "unused", "unknown"];
// what a known copy becomes when it changes, keeping its place
const NEXT = {you: "you-dead", them: "them-dead"};
const MARKS = {"you-dead": "🪦", "them-dead": "🪦", unused: "🔎"};

// each row's copies, as last drawn, and how long the log was, to tell a new game
let placed = null;

// how many copies of each kind of tile are each kind of copy
function count(view, me) {
  const them = me === "north" ? "south" : "north";
  const counts = {};
  for (const tile of view.tiles_in_game) {
    counts[tile] = Object.fromEntries(KINDS.map((kind) => [kind, 0]));
  }
  const add = (tile, kind) => {
    if (counts[tile]) {
      counts[tile][kind] += 1;
    }
  };
  for (const tile of [...view.tiles_in_hand[me], ...view.tiles_on_board[me]]) {
    add(tile, "you");
  }
  for (const tile of [...view.tiles_in_hand[them], ...view.tiles_on_board[them]]) {
    if (tile !== HIDDEN_TILE) {
      add(tile, "them");
    }
  }
  for (const turn of view.public_log) {
    for (const event of turn.events) {
      if (event.kind === "lose") {
        add(event.action, event.player === me ? "you-dead" : "them-dead");
      }
    }
  }
  for (const tile of view.unused_tiles) {
    if (tile !== HIDDEN_TILE) {
      add(tile, "unused");
    }
  }
  for (const tile of view.tiles_in_game) {
    const known = KINDS.reduce((sum, kind) => sum + counts[tile][kind], 0);
    counts[tile].unknown = Math.max(0, COPIES - known);
  }
  return counts;
}

// a row's copies, changing as few places as possible from how they were
function arrange(was, counts) {
  const left = {...counts};
  const row = Array(COPIES).fill(null);
  if (was) {
    // keep what's unchanged, from the right, so newly known copies take the left
    for (let i = COPIES - 1; i >= 0; i--) {
      if (left[was[i]] > 0) {
        row[i] = was[i];
        left[was[i]] -= 1;
      }
    }
    // a known copy that changed becomes what it changes into, where it was
    for (let i = 0; i < COPIES; i++) {
      const next = NEXT[was[i]];
      if (!row[i] && next && left[next] > 0) {
        row[i] = next;
        left[next] -= 1;
      }
    }
  }
  for (let i = 0; i < COPIES; i++) {
    if (!row[i]) {
      row[i] = KINDS.find((kind) => left[kind] > 0) || "unknown";
      left[row[i]] -= 1;
    }
  }
  return row;
}

// Draw the tray for `me` ("north" or "south"). A copy whose kind just changed is
// marked data-fresh, for animate.js.
function renderTray(tray, view, me) {
  const them = me === "north" ? "south" : "north";
  const counts = count(view, me);
  const newGame =
    !placed ||
    view.public_log.length < placed.logLength ||
    Object.keys(placed.rows).join("") !== view.tiles_in_game.join("");
  const rows = {};
  tray.replaceChildren();
  for (const tile of view.tiles_in_game) {
    const was = newGame ? null : placed.rows[tile];
    rows[tile] = arrange(was, counts[tile]);
    const row = document.createElement("div");
    row.className = "tray-row";
    row.dataset.tile = tile;
    const copies = document.createElement("div");
    copies.className = "tray-copies";
    const name = document.createElement("span");
    name.className = "tray-name";
    name.textContent = ACTION_NAMES[tile];
    row.append(copies, name);
    rows[tile].forEach((kind, i) => {
      const copy = document.createElement("span");
      copy.className = `tray-copy ${kind}`;
      copy.dataset.tile = tile;
      if (kind !== "unknown" && kind !== "unused") {
        copy.dataset.owner = kind.startsWith("you") ? me : them;
      }
      if (was && was[i] !== kind) {
        copy.dataset.fresh = kind;
      }
      const glyph = document.createElement("span");
      glyph.className = "tray-glyph";
      glyph.textContent = tile;
      copy.append(glyph);
      if (MARKS[kind]) {
        const mark = document.createElement("span");
        mark.className = "tray-mark";
        mark.textContent = MARKS[kind];
        copy.append(mark);
      }
      copies.append(copy);
    });
    tray.append(row);
  }
  placed = {rows, logLength: view.public_log.length};
}

export {renderTray};
