"use strict";

const ROWS = 5;
const COLUMNS = 5;

const NORTH_PLAYER = "north-player";
const SOUTH_PLAYER = "south-player";

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

function renderBoard(board, tiles) {
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
  for (const [row, col, char, player] of tiles) {
    const columnElement = board.querySelectorAll(".column")[col];
    const cellElement = columnElement.querySelectorAll(".cell")[row];
    if (!cellElement) {
      throw new Error(`${row}, ${col} out of bounds`);
    }
    cellElement.innerHTML = char;
    cellElement.classList = `cell ${player}`;
  }
}

export { createBoard, renderBoard };
