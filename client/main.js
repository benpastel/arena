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
  markChosenStart,
  markChosenAction,
  markChosenTarget,
} from "./renderSelection.js";

import {
  highlightSquares,
  highlightActions,
  highlightHand,
} from "./renderHighlights.js";


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

  const infoPanel = document.querySelector(".player-info");

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");
  joinGame(prompt, websocket);

  sendSelection(board, actionPanel, infoPanel, websocket);

  receiveSelection(board, actionPanel, websocket);

  receiveMoves(board, actionPanel, websocket);

  receivePrompt(prompt, websocket);

  receiveHighlights(board, actionPanel, infoPanel, websocket);
});

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function sendSelection(board, actionPanel, infoPanel, websocket) {
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
  infoPanel.addEventListener("click", ({ target }) => {
    const tile = target.dataset.tileName;
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
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    if (event.type === "SELECTION_CHANGE") {
      const player = event["player"];
      const start = event["start"];
      const action = event["action"];
      const target = event["target"];

      markChosenStart(board, start);
      markChosenAction(actionPanel, action);
      markChosenTarget(board, target, player);
    }
  });
}

function receiveHighlights(board, actionPanel, infoPanel, websocket) {
  // highlight possible squares, actions, responses, or tiles in hand
  // the server should call this again with empty lists to clear the highlights
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    if (event.type === "HIGHLIGHT_CHANGE") {
      const squares = event["squares"];
      const actions = event["actions"];
      const handTiles = event["handTiles"];

      highlightSquares(squares, board);
      highlightActions(actions, actionPanel);
      highlightHand(handTiles, infoPanel);
    }
  });
}

function receiveMoves(board, actionPanel, websocket) {
  // update the UI with changes to the persistent game state
  const log = document.querySelector(".log");

  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    if (event.type === "STATE_CHANGE") {
      const player_view = event["playerView"];

      renderBoard(board, player_view);
      renderLog(log, player_view);
      renderHand(player_view);
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

