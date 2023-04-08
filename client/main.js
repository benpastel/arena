// this websocket client runs in the player's browser
// it initializes the board, listens for moves, and sends moves to the server

import {
  createBoard,
  renderBoard,
  renderLog,
  renderHand,
  createActionPanel,
  NORTH_PLAYER,
  SOUTH_PLAYER,
} from "./renderState.js";

import {
  highlightOkActions,
  highlightOkTargets,
  markChosenStart,
  markChosenAction,
  markChosenTarget,
} from "./renderChoice.js";

// This counter identifies the most recent input request we've received from the server
// we include it in all outgoing changes so that the server can ignore anything stale.
//
// 0 means we aren't waiting for any input.
let CHOICE_ID = 0;

function joinGame(prompt, websocket) {
  websocket.addEventListener("open", () => {
    // send an "join" event informing the server which player we are
    // based on hardcoded url ?player=north or ?player=south
    // TODO: move to path
    const params = new URLSearchParams(window.location.search);
    const player = params.get("player");
    if (! (player === NORTH_PLAYER || player === SOUTH_PLAYER)) {
      const msg = `Please set the url param ?player=${NORTH_PLAYER} or ?player=${SOUTH_PLAYER}`;
      prompt.innerHTML = msg;
      console.log(params);
      throw new Error(msg);
    }
    const event = {
      type: "join",
      player
    };
    websocket.send(JSON.stringify(event));
  });
}

window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  const actionPanel = document.querySelector(".actions");
  createActionPanel(actionPanel);

  const prompt = document.querySelector(".prompt");
  prompt.innerHTML = "Waiting for other player to join.";

  const hand = document.querySelector(".hand");

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");
  joinGame(prompt, websocket);

  sendSelection(board, actionPanel, hand, websocket);

  receiveSelection(board, actionPanel, websocket);

  receiveMoves(board, actionPanel, document, websocket);

  receivePrompt(prompt, websocket);
});

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function sendSelection(board, actionPanel, hand, websocket) {
  // send all clicks on the board
  // and let the server decide if they are valid start/target selections
  board.addEventListener("click", ({ target }) => {
    const row = parseInt(target.dataset.row);
    const column = parseInt(target.dataset.column);
    if (!Number.isInteger(row) || !Number.isInteger(column)) {
      return;
    }
    websocket.send(
      JSON.stringify({
        choiceId: CHOICE_ID,
        data: {row, column}
      })
    );
  });

  // TODO:
  //  - fix action highlighting & include responses
  //  - send hand clicks to server
  //  - highlight selected tile for losing (wipe highlighted target?)
  //  - display challenge success/failure in prompt or log
  //  - disconnect BOTH players whenever either player disconnects (for now)
  //  - fix bug: hand click is not getting sent by 2nd player?  or after 1st tile lost?

  // send all clicks on the action panel
  // and let the server decide if they are valid actions or responses
  actionPanel.addEventListener("click", ({ target }) => {
    const button = target.dataset.name;
    if (button === undefined) {
      return;
    }
    websocket.send(
      JSON.stringify({
        choiceId: CHOICE_ID,
        data: {button}
      })
    );
  });

  // send all clicks in the hand
  // and let server decide if they are valid replacements for a lost tile
  //
  // clicks on the opponent's tiles are also sent, but they are Tile.HIDDEN so never valid
  hand.addEventListener("click", ({ target }) => {
    const tile = target.dataset.tileName;
    console.log(`Sending hand ${tile}`);
    if (tile === undefined) {
      return;
    }
    websocket.send(
      JSON.stringify({
        choiceId: CHOICE_ID,
        data: {tile}
      })
    );
  });
}

function receiveSelection(board, actionPanel, websocket) {
  // update the UI with changes to the current (partially) selected moves
  // TODO: simpler to pass the list of actions & targets separately?
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    if (event.type === "SELECTION_CHANGE") {
      const player = event["player"];
      const start = event["start"];
      const action = event["action"];
      const target = event["target"];
      const actionTargets = event["actionTargets"];

      markChosenStart(board, start);
      markChosenAction(actionPanel, action);
      markChosenTarget(board, target, player);

      highlightOkActions(actionPanel, actionTargets);
      if (action && actionTargets[action]) {
        highlightOkTargets(board, actionTargets[action]);
      } else {
        highlightOkTargets(board, []);
      }
    }
  });
}

function receiveMoves(board, actionPanel, doc, websocket) {
  // update the UI with changes to the persistent game state
  const log = doc.querySelector(".log");

  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    if (event.type === "STATE_CHANGE") {
      const player_view = event["playerView"];

      renderBoard(board, player_view);
      renderLog(log, player_view);
      renderHand(doc, player_view);
    }
  });
}

function receivePrompt(prompt, websocket) {
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);
    if (event.type === "PROMPT") {
      prompt.innerHTML = event.prompt;
      CHOICE_ID = parseInt(event.choiceId);
    }
  });
}

