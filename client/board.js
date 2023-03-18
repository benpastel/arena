"use strict";

const ROWS = 5;
const COLUMNS = 5;

const NORTH_PLAYER = "north-player";
const SOUTH_PLAYER = "south-player";
const PLAYERS = [NORTH_PLAYER, SOUTH_PLAYER];

// TODO get rows, columns, actions from server with game start event?
const ACTIONS = [
  "move",
  "smite",
  "🀥",
  "🀍",
  "🀐",
  "🀛",
  "🀒",
];

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
  for (const tile of ACTIONS) {
    const element = document.createElement("div")
    element.classList.add("action", tile);
    element.innerHTML = tile;
    action_panel.append(element);
  }
  return action_panel;
}

function renderBoard(board, player_view) {
  // TODO:
  //  - save references directly to the elements instead of querying them each time?
  //  - what's standard assert / error handling?
  //  - only change the elements that changed?

  // set board empty
  for (let c = 0; c < COLUMNS; c++) {
    const columnElement = board.querySelectorAll(".column")[c];
    for (let r = 0; r < ROWS; r++) {
      const cellElement = columnElement.querySelectorAll(".cell")[r];
      cellElement.innerHTML = "";
      cellElement.classList = "cell empty";
    }
  }
  // set player tiles
  for (const player of PLAYERS) {
    const tiles = player_view.tiles_on_board[player];
    const positions = player_view.positions[player];

    for (let t = 0; t < tiles.length; t++) {
      const char = tiles[t];
      const [row, col] = positions[t];

      const columnElement = board.querySelectorAll(".column")[col];
      const cellElement = columnElement.querySelectorAll(".cell")[row];

      if (!cellElement) {
        throw new Error(`Cell not found for ${row}, ${col}, ${char}`);
      }
      cellElement.innerHTML = char;
      cellElement.classList = `cell ${player}`;
    }
  }
}

function renderLog(panel, player_view) {
  panel.innerHTML = '<p>log<p>';
  for (const line of player_view.public_log) {
    panel.innerHTML += `<p>${line}</p>`;
  }
}

function renderHand(doc, player_view) {
  for (const player of PLAYERS) {
    const element = doc.querySelector(`.hand.${player}`);
    const hand = player_view.tiles_in_hand[player];
    const mana = player_view.mana[player];
    element.innerHTML = (
      `${hand.join(" ")}`
      + `<br />$${mana}`
    )
  }
}

function renderActions(board, action_panel, action_targets, player_view) {
  // TODO
}

export { createBoard, renderBoard, renderLog, renderHand, renderActions, createActionPanel };
