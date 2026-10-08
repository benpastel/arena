// this websocket client runs in the player's browser
// it shows the lobby and table room, then the board: it listens for moves, and sends
// moves to the server

import {
  createBoard,
  renderBoard,
  renderLog,
  renderHand,
  renderOther,
  renderWebs,
} from "./renderState.js";

import {renderSelection} from "./renderSelection.js";

import {
  highlightSquares,
  highlightActions,
  highlightHand,
  highlightBoardTiles,
} from "./renderHighlights.js";

import {setUpLobby, renderLobby, renderRoom} from "./lobby.js";

import {Net} from "./net.js";


// This counter identifies the most recent input request we've received from the server
// we include it in all outgoing changes so that the server can ignore anything stale.
//
// 0 means we aren't waiting for any input.
let CHOICE_ID = 0;

// remembered across visits, so a refresh puts you back in your seat
const ID_KEY = "arena.playerId";
const NAME_KEY = "arena.name";

function load(key) {
  try {
    return window.localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

function save(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // private windows may refuse; we just won't remember
  }
}

// the table in the url, which we join once we have a name
function hashTable() {
  const match = window.location.hash.match(/^#\/t\/([a-z0-9]+)/i);
  return match ? match[1] : null;
}

function setHash(hash) {
  if (window.location.hash !== hash) {
    window.history.replaceState(null, "", hash);
  }
}

// which screen is showing: "lobby", "room", or "game"
function showScreen(screen) {
  document.body.className = `at-${screen}`;
}

window.addEventListener("DOMContentLoaded", () => {
  const board = document.querySelector(".board");
  createBoard(board);

  const prompt = document.querySelector(".prompt");
  const infoPanel = document.querySelector(".player-info");
  const actionPanel = document.querySelector(".actions");
  const log = document.querySelector(".log");

  const lobby = document.querySelector(".lobby");
  const room = document.querySelector(".room");
  const nameInput = lobby.querySelector(".name-input");
  const netbar = document.querySelector(".netbar");
  const toast = document.querySelector(".toast");

  // the latest picks / claim, redrawn whenever the board is
  let selection = null;
  window.addEventListener("resize", () => renderSelection(board, actionPanel, selection));

  let welcomed = false;
  let table = null;
  let tables = [];
  let wantTable = hashTable();

  const named = () => nameInput.value.trim().length > 0;

  const net = new Net(
    () => ({type: "hello", playerId: load(ID_KEY) || null, name: load(NAME_KEY)}),
    onMessage,
    onStatus,
  );

  const actions = {
    join: (tableId) => net.send({type: "joinTable", tableId}),
    leave: () => net.send({type: "leaveTable"}),
    sit: (side) => net.send({type: "sit", side}),
    addBot: (side) => net.send({type: "addBot", side}),
    removeBot: (side) => net.send({type: "removeBot", side}),
    setTiles: (random, tiles) => net.send({type: "setTiles", random, tiles}),
    start: () => net.send({type: "start"}),
  };

  function maybeJoin() {
    if (welcomed && wantTable && named() && (!table || table.id !== wantTable)) {
      actions.join(wantTable);
    }
  }

  nameInput.value = load(NAME_KEY);
  nameInput.addEventListener("input", () => {
    const name = nameInput.value.trim();
    save(NAME_KEY, name);
    net.send({type: "setName", name});
    renderLobby(lobby, tables, named(), actions);
  });
  // a pasted table link joins once the name is entered, not on its first letter
  nameInput.addEventListener("change", maybeJoin);
  setUpLobby(lobby, () => net.send({type: "createTable"}));
  document.querySelector(".quit").addEventListener("click", () => {
    if (window.confirm("End this match for both players?")) {
      net.send({type: "quit"});
    }
  });

  window.addEventListener("hashchange", () => {
    wantTable = hashTable();
    maybeJoin();
  });

  function onStatus(status) {
    netbar.hidden = status === "open" || !welcomed;
    netbar.textContent = status === "replaced" ? "open in another tab" : "reconnecting…";
  }

  function onMessage(event) {
    switch (event.type) {
      case "welcome":
        welcomed = true;
        save(ID_KEY, event.playerId);
        if (document.activeElement !== nameInput) {
          nameInput.value = event.name;
        }
        maybeJoin();
        break;
      case "lobby":
        tables = event.tables;
        if (!table) {
          if (!wantTable) {
            setHash("#/");
          }
          renderLobby(lobby, tables, named(), actions);
          showScreen("lobby");
          if (!named()) {
            nameInput.focus();
          }
        }
        break;
      case "table":
        table = event.table;
        wantTable = table.id;
        setHash(`#/t/${table.id}`);
        if (table.playing) {
          showScreen("game");
        } else {
          renderRoom(room, table, actions);
          showScreen("room");
        }
        break;
      case "left":
        table = null;
        wantTable = null;
        setHash("#/");
        break;
      case "error":
        toast.textContent = event.message;
        toast.hidden = false;
        window.setTimeout(() => { toast.hidden = true; }, 2600);
        break;
      default:
        handleGameEvent(event);
    }
  }

  function handleGameEvent(event) {
    if (event.type === "STATE_CHANGE") {
      // update the UI with changes to the persistent game state
      const player_view = event["playerView"];

      renderBoard(board, player_view, actionPanel);
      renderLog(log, player_view);
      renderWebs(board, player_view);
      renderHand(player_view);
      renderOther(player_view);
      renderSelection(board, actionPanel, selection);
    } else if (event.type === "SELECTION_CHANGE") {
      // update the UI with changes to the current (partially) selected moves.
      // the server should call this again with null selections to clear the highlights.
      const {player, start, action, target} = event;
      selection = player || start || action || target ? {player, start, action, target} : null;
      renderSelection(board, actionPanel, selection);
    } else if (event.type === "HIGHLIGHT_CHANGE") {
      // highlight possible squares, actions, responses, or tiles in hand
      // the server should call this again with empty lists to clear the highlights
      highlightSquares(event["squares"], board, table?.mySide);
      highlightActions(event["actions"], actionPanel);
      highlightHand(event["handTiles"], infoPanel);
      highlightBoardTiles(event["boardTiles"], board);
    } else if (event.type === "PROMPT") {
      prompt.textContent = event.prompt;
      CHOICE_ID = parseInt(event.choiceId);

    } else if (event.type === "MATCH_CHANGE") {
      alert(event.message);
    }
  }

  sendSelection(board, actionPanel, infoPanel, net);

  net.connect();
});

function sendSelection(board, actionPanel, infoPanel, net) {
  // send all clicks on the board
  board.addEventListener("click", ({ target }) => {

    // send both the square's (row, column)
    // and the tile if it exists
    // and let the server decide if it's a valid start, target, or exchange tile
    const boardTile = target.closest("[data-tile-name]")?.dataset.tileName;
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

    net.send({
      choiceId: CHOICE_ID,
      data
    });
  });

  // send all clicks on the action panel
  // and let the server decide if they are valid actions or responses
  actionPanel.addEventListener("click", ({ target }) => {
    // the name under a button is part of it; its tooltip isn't
    const button = target.closest(".tooltiptext") ? undefined : target.closest("[data-name]")?.dataset.name;
    if (button === undefined) {
      return;
    }
    net.send({
      choiceId: CHOICE_ID,
      data: {button}
    });
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
    net.send({
      choiceId: CHOICE_ID,
      data: {handTile}
    });
  });
}
