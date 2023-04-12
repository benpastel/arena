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
const NORTH_TARGET = "target-north"; // a square is CHOSEN_TARGET by the north player
const SOUTH_TARGET = "target-south"; // a square is CHOSEN_TARGET by the south player

// must match python enums
const TILES = {
  "🀥": "🀥", // flower
  "🀐": "🀐", // bird
  "🀛": "🀛", // grenades
  "🀒": "🀒", // knives
  "🀍": "🀍", // hook
};
const OTHER_ACTIONS = {
  "↕": "↕", // move
  "⚡": "⚡", // smite
};
const RESPONSES = {
  "👍": "👍", // accept
  "🚩": "🚩", // challenge
};

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
  NORTH_TARGET,
  SOUTH_TARGET,
  TILES,
  OTHER_ACTIONS,
  RESPONSES,
};

