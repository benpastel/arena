"use strict";

// must match python state and CSS sizing assumptions
const ROWS = 5;
const COLUMNS = 5;

// must match css classes and python enums
const NORTH_PLAYER = "north";
const SOUTH_PLAYER = "south";
const PLAYERS = [NORTH_PLAYER, SOUTH_PLAYER];

// must match css classes
const HIGHLIGHT = "highlight"; // squares, actions, or tiles the player can select right now
const CHOSEN_START = "chosen-start"; // the square of the tile selected mid-turn
const CHOSEN_ACTION = "chosen-action"; // an action is selected mid-turn
const CHOSEN_TARGET = "chosen-target"; // a square is selected mid-turn as the target

// must match python enums
const TILES = {
  "🀥": "🀥", // flower
  "🀐": "🀐", // bird
  "🀛": "🀛", // grenades
  "🀒": "🀒", // knives
  "🀍": "🀍", // hook
};
const HIDDEN_TILE = "🀫";
const OTHER_ACTIONS = {
  "↕": "↕", // move
  "⚡": "⚡", // smite
};
const RESPONSES = {
  "👍": "👍", // accept
  "🚩": "🚩", // challenge
};

const TOOLTIPS = {
  "↕": "MOVE: move 1<br>gain $1",
  "⚡": "SMITE: pay $7<br>kill any enemy",
  "🀥": "FLOWER: move 1<br>gain $3",
  "🀐": "BIRD: move 2<br>gain $2",
  "🀛": "GRENADES: pay $3<br>kill 3x3 around empty square:<br>"
    + "<br>"
    + ". . X . .<br>"
    + ". . . . .<br>"
    + "X . O . X<br>"
    + ". . . . .<br>"
    + ". . X . .",
  "🀒": "KNIVES: pay $3 to kill:<br>"
    + "<br>"
    + ". X .<br>"
    + "X O X<br>"
    + ". X .<br>"
    + "<br>"
    + "or $5 to kill:<br>"
    + "<br>"
    + ". . X . .<br>"
    + ". X . X .<br>"
    + "X . O . X<br>"
    + ". X . X .<br>"
    + ". . X . .",
  "🀍": "HOOK: steal $2<br>in straight or diagonal line<br>blocked by HOOK",
  "👍": "ACCEPT",
  "🚩": "CHALLENGE",
}

export {
  ROWS,
  COLUMNS,
  NORTH_PLAYER,
  SOUTH_PLAYER,
  PLAYERS,
  HIGHLIGHT,
  CHOSEN_START,
  CHOSEN_ACTION,
  CHOSEN_TARGET,
  TILES,
  OTHER_ACTIONS,
  RESPONSES,
  HIDDEN_TILE,
  TOOLTIPS,
};

