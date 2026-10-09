"use strict";

import {
  ROWS,
  COLUMNS,
  TILES,
  PLAYERS,
  NORTH_PLAYER,
  SOUTH_PLAYER,
  HIDDEN_TILE,
  ACTION_NAMES,
  DESCRIPTIONS,
} from "./constants.js";


function createBoard(board, mySide) {
  // a 5x5 grid of squares, each knowing its own row and column; whoever is south sees
  // it as stored, and north sees it turned around, so your own side is always at the bottom
  board.innerHTML = "";
  const flip = mySide === NORTH_PLAYER;
  for (let i = 0; i < ROWS; i++) {
    for (let j = 0; j < COLUMNS; j++) {
      const row = flip ? ROWS - 1 - i : i;
      const column = flip ? COLUMNS - 1 - j : j;
      const cellElement = document.createElement("div");
      cellElement.className = "cell";
      cellElement.dataset.row = row;
      cellElement.dataset.column = column;
      board.append(cellElement);
    }
  }
  return board;
}

function setTooltip(element, text) {
  if (!element.classList.contains('tooltip')) {
    element.classList.add('tooltip');
    const textElement = document.createElement("span");
    textElement.classList.add('tooltiptext');
    textElement.innerHTML = text;
    element.append(textElement);
  } else {
    const textElement = element.querySelector(".tooltiptext");
    textElement.innerHTML = text;
  }
}


function addName(element, text) {
  // the small name under a button, shared by the game and the lobby
  const nameElement = document.createElement("span");
  nameElement.classList.add("action-name");
  nameElement.textContent = text;
  element.append(nameElement);
}

function findCell(board, row, col) {
  return board.querySelector(`.cell[data-row="${row}"][data-column="${col}"]`);
}

function addSquareMarks(cell, kind, contents) {
  // a special square keeps its piece where every square has it, full size and centred,
  // and marks itself in the bottom corners: the bonus on the left, or the exchange
  // tiles one in each corner
  cell.classList.add('special', kind);
  const marks = document.createElement("div");
  marks.classList.add("cell-marks");
  for (const content of contents) {
    const element = document.createElement("span");
    element.textContent = content;
    if (content in TILES || content === HIDDEN_TILE) {
      element.dataset.tileName = content;
      element.classList.add('board-tile');
    } else {
      element.classList.add('bonus');
    }
    marks.append(element);
  }
  cell.append(marks);
}

function renderBoard(board, player_view) {
  // set board empty
  for (const cell of board.querySelectorAll(".cell")) {
    cell.innerHTML = "";
    cell.classList.remove(NORTH_PLAYER, SOUTH_PLAYER, 'board-tile', 'special', 'bonus', 'exchange');
  }

  // create the bonus square
  const [bonusRow, bonusCol] = player_view.bonus_position;
  const bonusCell = findCell(board, bonusRow, bonusCol);
  const bonusText = '$'.repeat(player_view.bonus_amount) + '🔎'.repeat(player_view.bonus_reveal)

  addSquareMarks(bonusCell, 'bonus', [bonusText]);

  // create the exchange tile squares
  for (let p = 0; p < player_view.exchange_positions.length; p++) {
    const [exchangeRow, exchangeCol] = player_view.exchange_positions[p];
    const exchangeCell = findCell(board, exchangeRow, exchangeCol);
    addSquareMarks(exchangeCell, 'exchange', player_view.exchange_tiles[p]);
  }

  // set player tiles
  for (const player of PLAYERS) {
    const tiles = player_view.tiles_on_board[player];
    const positions = player_view.positions[player];

    for (let t = 0; t < tiles.length; t++) {
      const char = tiles[t];
      const [row, col] = positions[t];
      const cell = findCell(board, row, col);

      const piece = document.createElement("span");
      piece.classList.add("piece");
      piece.textContent = char;
      if (cell.classList.contains("exchange")) {
        // on an exchange square the piece is one of the tiles to choose between
        piece.dataset.tileName = char;
        piece.classList.add('board-tile');
      }
      cell.prepend(piece);
      cell.classList.add(player);
    }
  }
}

// how each kind of log event reads, after the name of the player it's about;
// must match python LogKind
const LOG_WORDS = {
  reflect: "reflects",
  reveal: "reveals",
  lose: "loses",
  exchange: "may have exchanged",
  web: "caught in web",
  skip: "skips turn",
  again: "goes again",
  x2: "×2 →",
  win: "wins",
  draw: "draw",
};

function logItem(glyph, name) {
  // a glyph with its small name beside it
  const item = document.createElement("span");
  item.className = "log-item";
  const glyphElement = document.createElement("span");
  glyphElement.className = "log-glyph";
  glyphElement.textContent = glyph;
  const nameElement = document.createElement("span");
  nameElement.className = "log-name";
  nameElement.textContent = name;
  item.append(glyphElement, nameElement);
  return item;
}

function logEventItem(event) {
  switch (event.kind) {
    case "challenge":
      return logItem("🚩", ACTION_NAMES["🚩"]);
    case "smite":
      return logItem("⚡", "SMITE");
    case "bonus":
      return logItem("$" + "🔎".repeat(event.count), "BONUS");
    default:
      return event.action ? logItem(event.action, ACTION_NAMES[event.action]) : null;
  }
}

function renderLogEvent(turnElement, event, names, showName) {
  const who = document.createElement("span");
  who.className = "log-who";
  if (event.player && showName) {
    who.classList.add(event.player);
    who.textContent = names[event.player];
    who.title = names[event.player];
  }

  const what = document.createElement("span");
  what.className = "log-what";
  what.classList.toggle("cancelled", event.cancelled);
  if (event.kind in LOG_WORDS) {
    what.append(LOG_WORDS[event.kind]);
  }
  const item = logEventItem(event);
  if (item) {
    what.append(item);
  }

  const coins = document.createElement("span");
  coins.className = "log-coins";
  for (const player of PLAYERS) {
    const delta = event.coins[player];
    if (delta) {
      const element = document.createElement("span");
      element.className = player;
      element.textContent = `${delta > 0 ? "+" : "−"}$${Math.abs(delta)}`;
      coins.append(element);
    }
  }

  turnElement.append(who, what, coins);
}

function renderLog(panel, player_view) {
  // one block per turn; every turn but the latest is faded
  const turns = player_view.public_log.filter((turn) => turn.events.length > 0);
  const latest = turns.findLastIndex((turn) => turn.player !== null);

  const list = document.createElement("div");
  list.className = "log-list";
  turns.forEach((turn, t) => {
    const turnElement = document.createElement("div");
    turnElement.className = "log-turn";
    turnElement.classList.toggle("old", t < latest);
    let previous = null;
    for (const event of turn.events) {
      // a player's name shows once for a run of their events
      renderLogEvent(turnElement, event, player_view.names, event.player !== previous);
      previous = event.player;
    }
    list.append(turnElement);
  });

  panel.replaceChildren(list);
  // scroll the log down to the bottom, so the latest line is visible
  panel.scrollTop = panel.scrollHeight;
}

function renderHand(player_view) {
  // each player's strip: name, coins, and the tiles in hand
  for (const player of PLAYERS) {
    const strip = document.querySelector(`.strip.${player}`);
    if (!strip) {
      continue;
    }
    const coins = player_view.coins[player];
    strip.querySelector(".name").textContent = player_view.names[player];
    strip.querySelector(".amount").textContent = `$${coins}`;

    // compare by contents, not just count: a rematch can deal a new hand with the
    // same number of tiles, and a length-only check would leave stale tiles (and
    // stale dataset.tileName) from the previous game in the DOM.
    const hand = player_view.tiles_in_hand[player];
    const panel = strip.querySelector(".hand-tiles");
    const currentTiles = Array.from(panel.children, (e) => e.dataset.tileName);
    const handChanged =
      hand.length !== currentTiles.length ||
      hand.some((tile, i) => tile !== currentTiles[i]);
    if (handChanged) {
      panel.innerHTML = "";
      for (const tile of hand) {
        const element = document.createElement("span");
        element.textContent = tile;
        element.dataset.tileName = tile;
        element.classList.add("hand-tile");
        panel.append(element);
      }
    }
  }
}

function renderWebs(board, player_view) {
  // clear all webs
  for (const cell of board.querySelectorAll(".cell")) {
    const existingWeb = cell.querySelector('.web');
    if (existingWeb) {
      cell.removeChild(existingWeb);
    }
  }

  // add webs for each player as background tints
  for (const player of PLAYERS) {
    const webs = player_view.webs[player];
    for (const [r, c] of webs) {
      const cell = findCell(board, r, c);

      const web = document.createElement('div');
      web.classList.add('web', player);
      cell.appendChild(web);
    }
  }
}

function renderOther(player_view) {
  document.querySelector(".unused-contents").textContent = player_view.unused_tiles.join("");
  document.querySelector(".discard-contents").textContent = player_view.discard.join("");
  document.querySelector(".hidden-tiles-contents").textContent = player_view.hidden_tiles.join("");
  document.querySelector(".in-play").textContent = player_view.tiles_in_game.join("");
  document.querySelector(".smite-cost .cost").textContent = `= $${player_view.smite_cost}`;
}

function renderRules(list, player_view) {
  // the reference: every tile in play, then moving and smiting, written out
  list.innerHTML = "";
  const entries = [...player_view.tiles_in_game, "↕", "⚡"];
  for (const glyph of entries) {
    const row = document.createElement("div");
    row.className = "rule";
    const glyphElement = document.createElement("span");
    glyphElement.className = "rule-glyph";
    glyphElement.textContent = glyph;
    const name = document.createElement("span");
    name.className = "rule-name";
    name.textContent = ACTION_NAMES[glyph];
    const text = document.createElement("span");
    text.className = "rule-text";
    text.textContent = glyph === "⚡"
      ? `on reaching $${player_view.smite_cost}, pay it to kill any enemy tile`
      : DESCRIPTIONS[glyph];
    row.append(glyphElement, name, text);
    list.append(row);
  }
}

export {createBoard, renderBoard, renderLog, renderHand, findCell, renderOther, renderRules, renderWebs, setTooltip, addName};
