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
} from "./renderGameState.js";

import {
  renderPrompt,
  highlightOkActions,
  highlightOkTargets,
  markChosenStart,
  markChosenAction,
  markChosenTarget,
  NEXT_CHOICE_START
} from "./renderChoice.js";

// Outgoing event type names.  Must match python.
const CHOOSE_START = "CHOOSE_START";
const CHOOSE_ACTION = "CHOOSE_ACTION";
const CHOOSE_TARGET = "CHOOSE_TARGET";


function joinGame(websocket) {
  websocket.addEventListener("open", () => {
    // send an "join" event informing the server which player we are
    // based on hardcoded url ?player=north or ?player=south
    const params = new URLSearchParams(window.location.search);
    const player = params["player"];
    if (! (player === NORTH_PLAYER || player === SOUTH_PLAYER)) {
      const msg = `Please set the url param ?player=${NORTH_PLAYER} or ?player=${SOUTH_PLAYER}`;
      alert(msg);
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
  renderPrompt(prompt, NEXT_CHOICE_START);

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");
  joinGame(websocket);

  sendChoices(board, actionPanel, websocket);

  receiveChoices(board, prompt, actionPanel, websocket);

  receiveMoves(board, actionPanel, document, websocket);
});

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function sendChoices(board, actionPanel, websocket) {
  // interpret clicks on board tiles or actions as possible selections
  // let server decide if they are valid
  board.addEventListener("click", ({ target }) => {
    const row = parseInt(target.dataset.row);
    const column = parseInt(target.dataset.column);
    if (!Number.isInteger(row) || !Number.isInteger(column)) {
      return;
    }
    // try interpreting click as either choosing a tile or choosing a target
    //
    // TODO remove type; add choice_id; put data into "data"
    websocket.send(
      JSON.stringify({
        type: CHOOSE_START,
        start: [row, column]
      })
    );
    websocket.send(
      JSON.stringify({
        type: CHOOSE_TARGET,
        target: [row, column]
      })
    );
  });

  actionPanel.addEventListener("click", ({ target }) => {
    const actionName = target.dataset.actionName;
    if (actionName === undefined) {
      return;
    }
    websocket.send(
      JSON.stringify({
        type: CHOOSE_ACTION,
        action: actionName
      })
    );
  });
}

function receiveChoices(board, prompt, actionPanel, websocket) {
  // update the UI with changes to the current (partially) selected moves
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    if (event.type === "ACTION_CHOICE_CHANGE") {
      const player = event["player"];
      const start = event["start"];
      const action = event["action"];
      const target = event["target"];
      const actionTargets = event["actionTargets"];
      const nextChoice = event["nextChoice"];

      markChosenStart(board, start);
      markChosenAction(actionPanel, action);
      markChosenTarget(board, target);

      renderPrompt(prompt, nextChoice);

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

    if (event.type === "GAME_STATE_CHANGE") {
      const player_view = event["playerView"];

      renderBoard(board, player_view);
      renderLog(log, player_view);
      renderHand(doc, player_view);
    }
  });
}
