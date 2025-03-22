// this websocket client runs in the player's browser
// it initializes the board, listens for moves, and sends moves to the server

import {
  NORTH_PLAYER,
  SOUTH_PLAYER,
  SOLO_MODE,
} from "./constants.js";

import {
  createBoard,
  renderBoard,
  renderLog,
  renderHand,
  createActionPanel,
  renderOther,
  renderHiddenTiles,
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
  highlightBoardTiles,
} from "./renderHighlights.js";


// This counter identifies the most recent input request we've received from the server
// we include it in all outgoing changes so that the server can ignore anything stale.
//
// 0 means we aren't waiting for any input.
let CHOICE_ID = 0;

function joinGame(prompt, websocket) {
  websocket.addEventListener("open", () => {
    // send an "join" event informing the server which player we are
    // based on hardcoded url ?player=north or ?player=south, or ?player=solo
    const params = new URLSearchParams(window.location.search);
    const player = params.get("player");
    if (! (player === NORTH_PLAYER || player === SOUTH_PLAYER || player === SOLO_MODE)) {
      const msg = `⚠️⚠️⚠️<br>Set your url to ?player=${NORTH_PLAYER} or ?player=${SOUTH_PLAYER} or ?player=${SOLO_MODE}<br>⚠️⚠️⚠️`;
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

function getWebSocketServer() {
  if (window.location.host === "localhost:8000") {
    return "ws://localhost:8001/";
  } else if (window.location.host === "benpastel.github.io" || window.location.host === "benpastel.com") {
    // github pages => heroku
    return "wss://benji-arena-7507cf3c8c79.herokuapp.com";
  } else {
    throw new Error(`Unsupported host: ${window.location.host}`);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  const actionPanel = document.querySelector(".actions");
  createActionPanel(actionPanel);

  const prompt = document.querySelector(".prompt");
  prompt.innerHTML = "⌛⌛⌛<br>Waiting for other player to join<br>⌛⌛⌛";

  const infoPanel = document.querySelector(".player-info");

  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket(getWebSocketServer());
  joinGame(prompt, websocket);

  sendSelection(board, actionPanel, infoPanel, websocket);

  receiveSelection(board, actionPanel, websocket);

  receiveMoves(board, actionPanel, websocket);

  receivePrompt(prompt, websocket);

  receiveHighlights(board, actionPanel, infoPanel, websocket);

  receiveGameOver(websocket);
});

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function sendSelection(board, actionPanel, infoPanel, websocket) {
  // send all clicks on the board
  board.addEventListener("click", ({ target }) => {

    // send both the square's (row, column)
    // and the tile if it exists
    // and let the server decide if it's a valid start, target, or exchange tile
    const boardTile = target.dataset.tileName;
    const cell = target.closest(".cell");
    const row = parseInt(cell.dataset.row);
    const column = parseInt(cell.dataset.column);

    const data = {};

    if (Number.isInteger(row) && Number.isInteger(column)) {
      data.row = row;
      data.column = column;
    }
    if (boardTile !== undefined) {
      data.boardTile = boardTile;
    }

    websocket.send(
      JSON.stringify({
        choiceId: CHOICE_ID,
        data
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
    const handTile = target.dataset.tileName;
    if (handTile === undefined) {
      return;
    }
    websocket.send(
      JSON.stringify({
        choiceId: CHOICE_ID,
        data: {handTile}
      })
    );
  });
}

function receiveSelection(board, actionPanel, websocket) {
  // update the UI with changes to the current (partially) selected moves.
  // the server should call this again with null selections to clear the highlights.
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);

    if (event.type === "SELECTION_CHANGE") {
      const player = event["player"];
      const start = event["start"];
      const action = event["action"];
      const target = event["target"];

      markChosenStart(board, start, player);
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
      const boardTiles = event["boardTiles"];

      highlightSquares(squares, board);
      highlightActions(actions, actionPanel);
      highlightHand(handTiles, infoPanel);
      highlightBoardTiles(boardTiles, board);
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
      renderHiddenTiles(player_view);
      renderHand(player_view);
      renderOther(player_view);
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

function receiveGameOver(websocket) {
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);
    if (event.type === "MATCH_CHANGE") {
      alert(event.message);
    }
  });
}

