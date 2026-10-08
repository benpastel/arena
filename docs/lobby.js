"use strict";

// The lobby (your name and the open tables) and the table room (seats and tiles,
// before the match starts).

import {
  NORTH_PLAYER,
  SOUTH_PLAYER,
  HIDDEN_TILE,
  TOOLTIPS,
  ALL_TILES,
  TILES_PER_GAME,
} from "./constants.js";

import {setTooltip} from "./renderState.js";


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

function button(text, onClick, disabled = false) {
  const b = element("button", "box-button", text);
  b.disabled = disabled;
  b.addEventListener("click", onClick);
  return b;
}

function tilesText(random, tiles) {
  // random tables show face-down tiles, since the set changes every game
  return random ? HIDDEN_TILE.repeat(TILES_PER_GAME) : tiles.join("");
}

function renderLobby(panel, tables, named, actions) {
  panel.querySelector(".new-table").disabled = !named;

  const list = panel.querySelector(".table-list");
  list.innerHTML = "";
  for (const table of tables) {
    const row = button("", () => actions.join(table.id), !named);
    row.classList.add("table-row");
    for (const side of [NORTH_PLAYER, SOUTH_PLAYER]) {
      if (table.seats[side] !== null) {
        row.append(element("span", `seat-name ${side}`, table.seats[side]));
      }
    }
    row.append(element("span", "table-tiles", tilesText(table.random, table.tiles)));
    list.append(row);
  }
}

function renderSeat(table, side, actions) {
  const seat = element("div", `seat ${side}`);
  const occupant = table.seats[side];

  if (occupant === null) {
    seat.append(button("sit", () => actions.sit(side)));
    if (table.amHost) {
      seat.append(button("bot", () => actions.addBot(side)));
    }
    return seat;
  }

  const name = element("span", "seat-name", occupant.name);
  if (!occupant.connected) {
    name.classList.add("gone");
  }
  seat.append(name);
  if (occupant.bot && table.amHost) {
    seat.append(button("×", () => actions.removeBot(side)));
  }
  return seat;
}

function renderPicker(table, actions) {
  const editable = table.amHost;
  const picker = element("div", "picker");

  const head = element("div", "picker-head");
  const random = button("random", () => actions.setTiles(!table.random, table.tiles), !editable);
  random.classList.toggle("on", table.random);
  head.append(random);
  if (editable && !table.random && table.tiles.length !== TILES_PER_GAME) {
    head.append(element("span", "tile-count", `${table.tiles.length}/${TILES_PER_GAME}`));
  }
  picker.append(head);

  const grid = element("div", "tile-grid");
  grid.classList.toggle("off", table.random);
  for (const [tile, name] of ALL_TILES) {
    const chosen = table.tiles.includes(tile);
    const choice = button("", () => {
      const tiles = chosen ? table.tiles.filter((t) => t !== tile) : [...table.tiles, tile];
      if (tiles.length <= TILES_PER_GAME) {
        actions.setTiles(table.random, tiles);
      }
    }, !editable || table.random);
    choice.classList.add("tile-choice");
    choice.classList.toggle("chosen", chosen);
    choice.append(element("span", "tile-glyph", tile), element("span", "tile-name", name));
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

  const buttons = element("div", "room-buttons");
  if (table.amHost) {
    buttons.append(button("start", actions.start, !(full && ready)));
  }
  buttons.append(button("leave", actions.leave));
  panel.append(buttons);

  if (!full) {
    const link = `${location.origin}${location.pathname}#/t/${table.id}`;
    const row = element("div", "link-row");
    row.append(element("code", "", link));
    const copy = button("copy", () => {
      navigator.clipboard?.writeText(link).then(() => {
        copy.textContent = "copied";
        window.setTimeout(() => { copy.textContent = "copy"; }, 1400);
      }, () => undefined);
    });
    row.append(copy);
    panel.append(row);
  }
}

export {renderLobby, renderRoom};
