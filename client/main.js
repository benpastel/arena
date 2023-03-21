// this websocket client runs in the player's browser
// it initializes the board, listens for moves, and sends moves to the server

import {
  createBoard,
  renderBoard,
  renderLog,
  renderHand,
  createActionPanel,
  NORTH_PLAYER
} from "./render.js";

import {
  ActionPicker
} from "./actionPicker.js";

window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  const actionPanel = document.querySelector(".actions");
  createActionPanel(actionPanel);

  const prompt = document.querySelector(".prompt");

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");

  // closure for sending moves to the server
  // called by ActionPicker when a player has successfully selected tile + action + target
  // on their turn
  function sendMoveFn(start, action, target) {
    event = {
      type: "action",
      start,
      action,
      target
    }
    websocket.send(JSON.stringify(event));
  }

  const actionPicker = new ActionPicker(prompt, sendMoveFn);
  actionPicker.beginWait();

  receiveMoves(board, actionPanel, document, websocket, actionPicker);

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

  // when clicking on an action, try to interpret it as choosing an action
  actionPanel.addEventListener("click", ({ target }) => {
    const actionName = target.dataset.actionName;
    if (actionName === undefined) {
      return;
    }
    actionPicker.tryChooseAction(actionName);
  });
});

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function receiveMoves(board, actionPanel, doc, websocket, actionPicker) {
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

        // TODO left off here
        // let's commit to ignoring player for starters?
        // and hardcoding it.  or reading current_player from the state directly
        // and see positions update.  also pass in actual actionTargets from event
        //
        // MEANWHILE also update UI to make action picking good
        //  - highlight selected tile
        //  - bold/gray valid/invalid actions
        //  - hardest part!  darken valid targets when hovering or selecting action
        const positions = player_view.positions[NORTH_PLAYER];
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
