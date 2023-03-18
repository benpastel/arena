// this websocket client runs in the player's browser
// it initializes the board, listens for moves, and sends moves to the server

import { createBoard, renderBoard, renderLog, renderHand, renderActions, createActionPanel } from "./board.js";

window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  const action_panel = document.querySelector(".actions");
  createActionPanel(action_panel);

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");

  receiveMoves(board, action_panel, document, websocket);

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

function receiveMoves(board, action_panel, doc, websocket) {
  const log = doc.querySelector(".log");

  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    switch (event.type) {
      case "state":
        // Update the UI with the new state.
        const player_view = event["player_view"];

        // TODO read action_target from event
        // list of action_target corresponding to positions[current_player]
        const action_targets = [
          {
            "smite": [[4,0], [4, 4]],
            "move": [[1, 0], [0, 1]],
            "🀥": [[1, 0], [0, 1]],
          },
          {
            "smite": [[4,0], [4, 4]],
            "move": [[0, 3], [1, 4]],
            "🀥": [[0, 3], [1, 4]],
          }
        ];

        // console.log(player_view);
        renderBoard(board, player_view);
        renderLog(log, player_view);
        renderHand(doc, player_view);
        renderActions(board, action_panel, action_targets, player_view);
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
