// this websocket client runs in the player's browser
// it initializes the board, listens for moves, and sends moves to the server

import { createBoard, renderBoard } from "./board.js";

window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");

  receiveMoves(board, websocket);

  sendMoves(board, websocket);
});

function sendMoves(board, websocket) {
  // When clicking a column, send a "play" event for a move in that column.
  board.addEventListener("click", ({ target }) => {
    const column = target.dataset.column;
    // Ignore clicks outside a column.
    if (column === undefined) {
      return;
    }
    const event = {
      type: "play",
      column: parseInt(column, 10),
    };
    websocket.send(JSON.stringify(event));
  });
}

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function receiveMoves(board, websocket) {
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    switch (event.type) {
      case "state":
        // Update the UI with the new state.

        // TODO: get tiles from data instead
        const tiles = [
          [0, 0, "🀫", "north-player"],
          [0, 4, "🀫", "north-player"],
          [4, 0, "🀥", "south-player"],
          [4, 4, "🀛", "south-player"],
        ]
        renderBoard(board, tiles);

        break;
      case "win":
        showMessage(`Player ${event.player} wins!`);
        // No further messages are expected; close the WebSocket connection.
        websocket.close(1000);
        break;
      case "error":
        showMessage(event.message);
        break;
      default:
        throw new Error(`Unsupported event type: ${event.type}.`);
    }
  });
}
