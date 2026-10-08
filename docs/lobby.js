"use strict";

// The lobby (your name and the open tables) and the table room (seats and tiles,
// before the match starts).
//
// Every control is drawn like the game's buttons: an icon in a tile-like shell,
// with its name under it.

import {
  NORTH_PLAYER,
  SOUTH_PLAYER,
  HIDDEN_TILE,
  TOOLTIPS,
  ALL_TILES,
  TILES_PER_GAME,
} from "./constants.js";

import {setTooltip, addName} from "./renderState.js";

// icons for the lobby's buttons; the game's own buttons are its tiles and responses
const ICONS = {
  newTable: "+",
  sit: "🪑",
  bot: "🤖",
  remove: "X",
  random: "🎲",
  // text presentation, so it stays a plain black triangle rather than an emoji
  start: "▶︎",
  leave: "←",
  copy: "📋",
};


function element(tag, className, text) {
  const e = document.createElement(tag);
  if (className) {
    e.className = className;
  }
  if (text !== undefined) {
    e.textContent = text;
  }
  return e;
}

function iconButton(icon, name, onClick, disabled = false) {
  const b = element("button", "outlined-button", icon);
  addName(b, name);
  b.disabled = disabled;
  b.addEventListener("click", onClick);
  return b;
}

function row(...children) {
  const r = element("div", "button-row");
  r.append(...children);
  return r;
}

function tilesText(random, tiles) {
  // random tables show face-down tiles, since the set changes every game
  return random ? HIDDEN_TILE.repeat(TILES_PER_GAME) : tiles.join("");
}

function setUpLobby(panel, onNewTable) {
  // the static parts of the lobby: the name field and the new table button
  addName(panel.querySelector(".name-field"), "NAME");
  panel.querySelector(".new-table-row").append(
    iconButton(ICONS.newTable, "NEW TABLE", onNewTable, true),
  );
}

function renderLobby(panel, tables, named, actions) {
  panel.querySelector(".new-table-row .outlined-button").disabled = !named;

  const list = panel.querySelector(".table-list");
  list.innerHTML = "";
  for (const table of tables) {
    const joinButton = iconButton("", "JOIN", () => actions.join(table.id), !named);
    joinButton.classList.add("table-row");
    for (const side of [NORTH_PLAYER, SOUTH_PLAYER]) {
      if (table.seats[side] !== null) {
        joinButton.append(element("span", `seat-name ${side}`, table.seats[side]));
      }
    }
    joinButton.append(element("span", "table-tiles", tilesText(table.random, table.tiles)));
    list.append(joinButton);
  }
}

function renderSeat(table, side, actions) {
  const seat = element("div", `seat ${side}`);
  const occupant = table.seats[side];

  if (occupant === null) {
    const buttons = [iconButton(ICONS.sit, "SIT", () => actions.sit(side))];
    if (table.amHost) {
      buttons.push(iconButton(ICONS.bot, "BOT", () => actions.addBot(side)));
    }
    seat.append(row(...buttons));
    return seat;
  }

  const name = element("span", "seat-name", occupant.name);
  if (!occupant.connected) {
    name.classList.add("gone");
  }
  seat.append(name);
  if (occupant.bot && table.amHost) {
    seat.append(iconButton(ICONS.remove, "REMOVE", () => actions.removeBot(side)));
  }
  return seat;
}

function renderPicker(table, actions) {
  const editable = table.amHost;
  const picker = element("div", "picker");

  const random = iconButton(ICONS.random, "RANDOM", () => actions.setTiles(!table.random, table.tiles), !editable);
  random.classList.toggle("on", table.random);
  const head = row(random);
  if (editable && !table.random && table.tiles.length !== TILES_PER_GAME) {
    head.append(element("span", "tile-count", `${table.tiles.length}/${TILES_PER_GAME}`));
  }
  picker.append(head);

  const grid = element("div", "tile-grid");
  grid.classList.toggle("off", table.random);
  for (const [tile, name] of ALL_TILES) {
    const chosen = table.tiles.includes(tile);
    const choice = element("button", "tile-button tile-choice", tile);
    choice.classList.toggle("chosen", chosen);
    choice.disabled = !editable || table.random;
    choice.addEventListener("click", () => {
      const tiles = chosen ? table.tiles.filter((t) => t !== tile) : [...table.tiles, tile];
      if (tiles.length <= TILES_PER_GAME) {
        actions.setTiles(table.random, tiles);
      }
    });
    addName(choice, name);
    setTooltip(choice, TOOLTIPS[tile]);
    grid.append(choice);
  }
  picker.append(grid);
  return picker;
}

function renderRoom(panel, table, actions) {
  panel.innerHTML = "";

  // north on top and south below, as on the board
  panel.append(
    renderSeat(table, NORTH_PLAYER, actions),
    renderPicker(table, actions),
    renderSeat(table, SOUTH_PLAYER, actions),
  );

  const full = table.seats[NORTH_PLAYER] !== null && table.seats[SOUTH_PLAYER] !== null;
  const ready = table.random || table.tiles.length === TILES_PER_GAME;

  const buttons = [];
  if (table.amHost) {
    buttons.push(iconButton(ICONS.start, "START", actions.start, !(full && ready)));
  }
  buttons.push(iconButton(ICONS.leave, "LEAVE", actions.leave));
  panel.append(row(...buttons));

  if (!full) {
    const link = `${location.origin}${location.pathname}#/t/${table.id}`;
    const copy = iconButton(ICONS.copy, "COPY", () => {
      navigator.clipboard?.writeText(link).then(() => {
        copy.querySelector(".action-name").textContent = "COPIED";
        window.setTimeout(() => { copy.querySelector(".action-name").textContent = "COPY"; }, 1400);
      }, () => undefined);
    });
    const linkRow = element("div", "link-row");
    linkRow.append(copy, element("code", "", link));
    panel.append(linkRow);
  }
}

export {setUpLobby, renderLobby, renderRoom};
