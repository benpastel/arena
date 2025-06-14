"use strict";

import {
  ROWS,
  COLUMNS,
  OTHER_ACTIONS,
  TILES,
  RESPONSES,
  PLAYERS,
  NORTH_PLAYER,
  SOUTH_PLAYER,
  HIDDEN_TILE,
  TOOLTIPS,
} from "./constants.js";


function createBoard(board) {
  // Generate board.
  for (let column = 0; column < COLUMNS; column++) {
    const columnElement = document.createElement("div");
    columnElement.className = "column";
    columnElement.dataset.column = column;
    for (let row = 0; row < ROWS; row++) {
      const cellElement = document.createElement("div");
      cellElement.className = "cell";
      cellElement.dataset.row = row;
      cellElement.dataset.column = column;
      columnElement.append(cellElement);
    }
    board.append(columnElement);
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


function createActionPanel(action_panel, tiles) {
  // delete old action panel contents
  for (const element of action_panel.querySelectorAll("div")) {
    action_panel.removeChild(element);
  }

  for (const name in OTHER_ACTIONS) {
    const element = document.createElement("div");
    element.innerHTML = OTHER_ACTIONS[name];
    element.dataset.name = name;
    element.classList = "outlined-button";
    action_panel.append(element);
    setTooltip(element, TOOLTIPS[name]);
  }
  const sep1 = document.createElement('div');
  sep1.classList = "action-separator";
  action_panel.append(sep1);
  for (const name of tiles) {
    const element = document.createElement("div");
    element.innerHTML = TILES[name];
    element.dataset.name = name;
    element.classList = "tile-button";
    action_panel.append(element);
    setTooltip(element, TOOLTIPS[name]);
  }
  const sep2 = document.createElement('div');
  sep2.classList = "action-separator";
  action_panel.append(sep2);
  for (const name in RESPONSES) {
    const element = document.createElement("div");
    element.innerHTML = RESPONSES[name];
    element.dataset.name = name;
    element.classList = "outlined-button";
    action_panel.append(element);
    setTooltip(element, TOOLTIPS[name]);
  }
  return action_panel;
}

function findCell(board, row, col) {
  // input: board element, row index, col index
  // returns the cell element corresponding to the square
  const columnElement = board.querySelectorAll(".column")[col];
  return columnElement.querySelectorAll(".cell")[row];
}

function addSpecialBottomRow(cell, contents) {
  // convert board cell to two rows and add exchange tiles or bonus to the bottom row
  //
  // `contents`: array to set inner html of the new elements
  // also set the tileName to those contents if they are tiles
  cell.classList.add('special');

  const topRow = document.createElement("div");
  topRow.classList = 'specialRow topRow';
  cell.append(topRow);

  // put an empty div in the top row to hold the vertical space
  const empty = document.createElement("div");
  empty.innerHTML = '​';
  topRow.append(empty);

  const bottomRow = document.createElement("div");
  bottomRow.classList = 'specialRow bottomRow';
  cell.append(bottomRow);

  for (const content of contents) {
    const element = document.createElement("div");
    element.innerHTML = content;
    if (content in TILES || content === HIDDEN_TILE) {
      element.dataset.tileName = content;
      element.classList.add('board-tile');
    }
    // shrink font size if content is too long
    if (content.length >= 8) {
      element.style.fontSize = '3vmin';
    } else if (content.length >= 6) {
      element.style.fontSize = '4vmin';
    } else if (content.length >= 3) {
      element.style.fontSize = '5vmin';
    }
    bottomRow.append(element);
  }
}

function renderBoard(board, player_view, action_panel) {
  const tiles = player_view.tiles_in_game;
  createActionPanel(action_panel, tiles);

  // set board empty
  for (const cell of board.querySelectorAll(".cell")) {
    cell.innerHTML = "";
    cell.classList.remove(NORTH_PLAYER, SOUTH_PLAYER, 'board-tile', 'special');
  }

  // create the bonus square
  const [bonusRow, bonusCol] = player_view.bonus_position;
  const bonusCell = findCell(board, bonusRow, bonusCol);
  const bonusText = '$'.repeat(player_view.bonus_amount) + '🔎'.repeat(player_view.bonus_reveal)

  addSpecialBottomRow(bonusCell, [bonusText]);

  // create the exchange tile squares
  for (let p = 0; p < player_view.exchange_positions.length; p++) {
    const [exchangeRow, exchangeCol] = player_view.exchange_positions[p];
    const exchangeCell = findCell(board, exchangeRow, exchangeCol);
    addSpecialBottomRow(exchangeCell, player_view.exchange_tiles[p]);
  }

  // set player tiles
  for (const player of PLAYERS) {
    const tiles = player_view.tiles_on_board[player];
    const positions = player_view.positions[player];

    for (let t = 0; t < tiles.length; t++) {
      const char = tiles[t];
      const [row, col] = positions[t];
      const cell = findCell(board, row, col);

      let container;
      if (cell.classList.contains("special")) {
        // put the tile in the top row
        // also annotate the tile for exchanges
        container = cell.querySelector('.topRow');
        container.dataset.tileName = char;
        container.classList.add('board-tile');
      } else {
        // put the tile directly in the cell
        container = cell;
      }
      container.innerHTML = char;
      container.classList.add(player);
    }
  }
}

function renderLog(panel, player_view) {
  panel.innerHTML = '';
  for (const line of player_view.public_log) {
    panel.innerHTML += `<p>${line}</p>`;
  }
  // scroll the log down to the bottom, so the latest line is visible
  panel.scrollTop = panel.scrollHeight;
}

function renderHand(player_view) {
  for (const player of PLAYERS) {
    const coins = player_view.coins[player];
    const hand = player_view.tiles_in_hand[player];

    const panel = document.querySelector(`.hand.${player}`);
    const tileElements = panel.querySelectorAll('.hand-tile');
    const coinElement = panel.querySelector('.coins');
    coinElement.innerHTML = `$${coins}/${player_view.smite_cost}`;

    if (hand.length !== tileElements.length) {
      // hand changed since the last render
      // redraw from scratch
      for (const element of tileElements) {
        panel.removeChild(element);
      }
      for (const tile of hand) {
        const element = document.createElement("span");
        element.innerHTML = tile;
        element.dataset.tileName = tile;
        element.classList.add('hand-tile');
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
  const unusedPanel = document.querySelector('.unused');
  setTooltip(unusedPanel, 'Tiles unused this game.');

  const unusedContents = document.querySelector('.unused-contents');
  unusedContents.innerHTML = 'unused: ';
  for (const tile of player_view.unused_tiles) {
    unusedContents.innerHTML += tile;
  }

  const discardPanel = document.querySelector('.discard');
  setTooltip(discardPanel, 'Tiles discarded from play.');

  const discardContents = document.querySelector('.discard-contents');
  discardContents.innerHTML = 'discarded: ';
  for (const tile of player_view.discard) {
    discardContents.innerHTML += tile;
  }

  const hiddenPanel = document.querySelector('.hidden-tiles');
  setTooltip(hiddenPanel, 'All the tiles currently unknown to you.');

  const contents = document.querySelector('.hidden-tiles-contents');
  contents.innerHTML = 'unknown to you: ';
  for (const tile of player_view.hidden_tiles) {
    contents.innerHTML += tile;
  }
}


export {createBoard, renderBoard, renderLog, renderHand, createActionPanel, findCell, renderOther, renderWebs};
