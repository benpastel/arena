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

function createActionPanel(action_panel) {

  for (const name in OTHER_ACTIONS) {
    const element = document.createElement("div");
    element.innerHTML = OTHER_ACTIONS[name];
    element.dataset.name = name;
    element.classList.add("outlined-button");
    action_panel.append(element);
  }
  const sep1 = document.createElement('div');
  sep1.classList.add("action-separator");
  action_panel.append(sep1);
  for (const name in TILES) {
    const element = document.createElement("div");
    element.innerHTML = TILES[name];
    element.dataset.name = name;
    element.classList.add("tile-button");
    action_panel.append(element);
  }
  const sep2 = document.createElement('div');
  sep2.classList.add("action-separator");
  action_panel.append(sep2);
  for (const name in RESPONSES) {
    const element = document.createElement("div");
    element.innerHTML = RESPONSES[name];
    element.dataset.name = name;
    element.classList.add("outlined-button");
    action_panel.append(element);
  }
  return action_panel;
}

function findCell(board, row, col) {
  // input: board element, row index, col index
  // returns the cell element corresponding to the square
  const columnElement = board.querySelectorAll(".column")[col];
  return columnElement.querySelectorAll(".cell")[row];
}

function renderBoard(board, player_view) {
  // TODO:
  //  - save references directly to the elements instead of querying them each time?
  //  - what's standard assert / error handling?
  //  - only change the elements that changed?

  // set board empty
  for (const cell of board.querySelectorAll(".cell")) {
    cell.innerHTML = "";
    cell.classList = "cell invalid-target";
  }
  // draw special board tiles
  // these are overwritten by player tiles
  // TODO don't redraw every time?

  const [bonusRow, bonusCol] = player_view.bonus_position;
  const bonusCell = findCell(board, bonusRow, bonusCol);
  bonusCell.classList.add('book');

  const bonusElement = document.createElement("div");
  bonusElement.innerHTML = "+1";
  bonusElement.classList = "bonus";
  bonusCell.append(bonusElement);

  for (let p = 0; p < player_view.book_positions.length; p++) {
    const [bookRow, bookCol] = player_view.book_positions[p];
    const bookCell = findCell(board, bookRow, bookCol);
    bookCell.classList.add('book');

    for (const bookTile of player_view.book_tiles[p]) {

      // TODO find or create this element
      const element = document.createElement("div");
      element.classList = `bookTile ${bookTile}`;
      element.innerHTML = bookTile;

      bookCell.append(element);
    }
  }

  // set player tiles
  for (const player of PLAYERS) {
    const tiles = player_view.tiles_on_board[player];
    const positions = player_view.positions[player];

    for (let t = 0; t < tiles.length; t++) {
      const char = tiles[t];
      const [row, col] = positions[t];
      const cell = findCell(board, row, col);
      cell.innerHTML = char;
      cell.classList.remove(NORTH_PLAYER, SOUTH_PLAYER);
      cell.classList.add(player);
    }
  }
}

function renderLog(panel, player_view) {
  panel.innerHTML = '';
  for (const line of player_view.public_log) {
    panel.innerHTML += `<p>${line}</p>`;
  }
}

function renderHand(player_view) {
  for (const player of PLAYERS) {
    const coins = player_view.coins[player];
    const hand = player_view.tiles_in_hand[player];

    const panel = document.querySelector(`.hand.${player}`);
    const tileElements = panel.querySelectorAll('.hand-tile');
    const coinElement = panel.querySelector('.coins');
    coinElement.innerHTML = `$${coins}`;

    if (hand.length !== tileElements.length) {
      // hand changed since the last render
      // redraw from scratch
      for (const element of tileElements) {
        panel.removeChild(element);
      }
      for (const tile of hand) {
        const element = document.createElement("div");
        element.innerHTML = tile;
        element.dataset.tileName = tile;
        element.classList.add('hand-tile');
        panel.append(element);
      }
    }
  }
}

export {createBoard, renderBoard, renderLog, renderHand, createActionPanel};
