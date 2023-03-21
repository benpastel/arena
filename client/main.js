// this websocket client runs in the player's browser
// it initializes the board, listens for moves, and sends moves to the server

import {
  createBoard,
  renderBoard,
  renderLog,
  renderHand,
  createActionPanel
} from "./render.js";

import {
  ActionPicker
} from "./actionPicker.js";

window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  const action_panel = document.querySelector(".actions");
  createActionPanel(action_panel);

  const prompt = document.querySelector(".prompt");

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");

  // closure for sending moves to the server
  // called by ActionPicker when a player has successfully selected tile + action + target
  // on their turn
  function sendMoveFn(tile, action, target) {
    event = {
      type: "action",
      tile,
      action,
      target
    }
    websocket.send(JSON.stringify(event));
  }

  const actionPicker = new ActionPicker(prompt, sendMoveFn);
  actionPicker.beginWait();

  receiveMoves(board, action_panel, document, websocket, actionPicker);

  // event listeners for ActionPicker
  // when clicking on an action, try to interpret it as choosing an action

  // when clicking on a tile, try to interpret it as choosing a tile OR choosing a target
  board.addEventListener("click", ({ target }) => {
    const row = parseInt(target.dataset.row);
    const column = parseInt(target.dataset.column);
    if (!Number.isInteger(row) || !Number.isInteger(column)) {
      return;
    }
    actionPicker.tryChooseTile(row, column);
    actionPicker.tryChooseTarget(row, column);
  });
});

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function receiveMoves(board, action_panel, doc, websocket, actionPicker) {
  const log = doc.querySelector(".log");

  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    switch (event.type) {
      case "state":
        // Update the UI with the new state.
        const player_view = event["player_view"];

        renderBoard(board, player_view);
        renderLog(log, player_view);
        renderHand(doc, player_view);

        // TODO read these from event
        // TODO distinguish between a state update that means it's our turn to play
        // and one that means we've just played
        const positions = [
          [0, 0],
          [0, 4],
        ];
        const actionTargets = [
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
        actionPicker.beginChooseTile(positions, actionTargets);
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
