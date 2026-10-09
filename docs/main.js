// this websocket client runs in the player's browser
// it shows the lobby and table room, then the board: it listens for moves, and sends
// moves to the server

import {
  createBoard,
  renderBoard,
  renderLog,
  renderHand,
  renderOther,
  renderRules,
  renderWebs,
} from "./renderState.js";

import {renderSelection} from "./renderSelection.js";

import {
  highlightSquares,
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

// the opponent's side, given ours
function otherSide(side) {
  return side === "north" ? "south" : "north";
}

window.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".container");
  const board = document.querySelector(".board");
  const topStrip = container.querySelector(".strip.top");
  const bottomStrip = container.querySelector(".strip.bottom");
  const log = document.querySelector(".log");
  const rules = document.querySelector(".rules");

  // the board and strips are drawn from our side: ours at the bottom, theirs at the top
  let orientation = null;
  let lastView = null;
  function orient(mySide) {
    const side = mySide || "south";
    if (side === orientation) {
      return;
    }
    orientation = side;
    container.classList.toggle("me-north", side === "north");
    for (const [strip, owner] of [[topStrip, otherSide(side)], [bottomStrip, side]]) {
      strip.classList.remove("north", "south");
      strip.classList.add(owner);
    }
    createBoard(board, side);
    if (lastView) {
      renderGame(lastView);
    }
  }
  orient("south");

  const lobby = document.querySelector(".lobby");
  const room = document.querySelector(".room");
  const nameInput = lobby.querySelector(".name-input");
  const netbar = document.querySelector(".netbar");
  const toast = document.querySelector(".toast");

  // the latest picks / claim, redrawn whenever the board is
  // and the latest highlights, whose actions and targets are drawn on the board too
  let selection = null;
  let highlight = null;
  const redrawSelection = () => renderSelection(board, selection, highlight);

  function renderGame(player_view) {
    renderBoard(board, player_view);
    renderLog(log, player_view);
    renderWebs(board, player_view);
    renderHand(player_view);
    renderOther(player_view);
    renderRules(rules.querySelector(".rules-list"), player_view);
    redrawSelection();
  }

  // the turn is shown in the strip of whoever the game is waiting on, with the prompt
  // written in it
  function showTurn(promptText, choiceId) {
    const waiting = "Waiting for opponent to ";
    let acting = null;
    let note = "";
    if (choiceId > 0) {
      acting = bottomStrip;
      note = promptText;
    } else if (promptText.startsWith(waiting)) {
      acting = topStrip;
      const rest = promptText.slice(waiting.length);
      note = rest.charAt(0).toUpperCase() + rest.slice(1);
    }
    for (const strip of [topStrip, bottomStrip]) {
      strip.classList.toggle("acting", strip === acting);
      strip.querySelector(".turn-note").textContent = strip === acting ? note : "";
    }
  }
  window.addEventListener("resize", redrawSelection);

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
  // the reference for the tiles in play: one click opens it over most of the screen
  const openRules = () => { rules.hidden = false; };
  const closeRules = () => { rules.hidden = true; };
  document.querySelector(".in-play").addEventListener("click", openRules);
  rules.querySelector(".rules-close").addEventListener("click", closeRules);
  rules.addEventListener("click", ({ target }) => {
    if (target === rules) {
      closeRules();
    }
  });
  window.addEventListener("keydown", ({ key }) => {
    if (key === "Escape") {
      closeRules();
    }
  });

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
          orient(table.mySide);
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
      lastView = event["playerView"];
      renderGame(lastView);
    } else if (event.type === "SELECTION_CHANGE") {
      // update the UI with changes to the current (partially) selected moves.
      // the server should call this again with null selections to clear the highlights.
      const {player, start, action, target, reflect} = event;
      selection = player || start || action || target ? {player, start, action, target, reflect} : null;
      redrawSelection();
    } else if (event.type === "HIGHLIGHT_CHANGE") {
      // highlight possible squares or tiles; actions and responses are drawn on the
      // board, and the action panel below it is only for reference
      // the server should call this again with empty lists to clear the highlights
      highlight = event;
      highlightSquares(event["squares"], board, table?.mySide);
      highlightHand(event["handTiles"], container);
      highlightBoardTiles(event["boardTiles"], board);
      redrawSelection();
    } else if (event.type === "PROMPT") {
      CHOICE_ID = parseInt(event.choiceId);
      showTurn(event.prompt, CHOICE_ID);
    } else if (event.type === "MATCH_CHANGE") {
      alert(event.message);
    }
  }

  sendSelection(board, container, net);

  net.connect();
});

function sendSelection(board, container, net) {
  // send all clicks on the board
  board.addEventListener("click", ({ target }) => {
    // an ability or response drawn on the board; one in a square also picks that square
    const option = target.closest(".option");
    if (option) {
      const data = {button: option.dataset.name};
      const optionCell = option.closest(".cell");
      if (optionCell) {
        data.row = parseInt(optionCell.dataset.row);
        data.column = parseInt(optionCell.dataset.column);
      }
      net.send({choiceId: CHOICE_ID, data});
      return;
    }
    if (target.closest(".claim-note")) {
      return;
    }

    // send both the square's (row, column)
    // and the tile if it exists
    // and let the server decide if it's a valid start, target, or exchange tile
    const boardTile = target.closest("[data-tile-name]")?.dataset.tileName;
    const cell = target.closest(".cell");
    if (!cell) {
      return;
    }
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

  // send all clicks in the hand
  // and let server decide if they are valid replacements for a lost tile
  //
  // clicks on the opponent's tiles are also sent, but they are Tile.HIDDEN so never valid
  container.addEventListener("click", ({ target }) => {
    const handTile = target.closest(".hand-tile")?.dataset.tileName;
    if (handTile === undefined) {
      return;
    }
    net.send({
      choiceId: CHOICE_ID,
      data: {handTile}
    });
  });
}
