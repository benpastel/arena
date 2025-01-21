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

// TODO: this list should include all tiles, and the tiles chosen for the game should be read
// from the state.  For now I'm just hardcoding the active tiles.
// must match python enums
const TILES = {
  // "🀥": "🀥", // flower
  "🀐": "🀐", // bird
  // "🀛": "🀛", // grenades
  // "🀒": "🀒", // knives
  "🀍": "🀍", // hook
  "🀨": "🀨", // harvester
  "🀗": "🀗", // backstabber
  "🀙": "🀙", // fireball
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
  "↕": "MOVE<br>move 1<br>gain $1",
  "⚡": "SMITE<br>pay $7<br>kill any enemy",
  "🀥": "FLOWER<br>gain $3<br>"
    + "move to an X:<br>"
    + "<br>"
    + "X X X<br>"
    + "X 🀥 X<br>"
    + "X X X<br>",
  "🀐": "BIRD<br>gain $2<br>"
    + "reveal 1 unused tile<br>"
    + "move to an X:<br>"
    + "<br>"
    + ". . X . .<br>"
    + ". X X X .<br>"
    + "X X 🀛 X X<br>"
    + ". X X X .<br>"
    + ". . X . .",
  "🀛": "GRENADES<br>pay $3<br>"
    + "roll a grenade to the X if unobstructed and explode a 3x3 square:<br>"
    + "<br>"
    + ". . X . .<br>"
    + ". . . . .<br>"
    + "X . 🀛 . X<br>"
    + ". . . . .<br>"
    + ". . X . .",
  "🀒": "KNIVES<br>pay the amount shown to kill:<br>"
    + "<br>"
    + ". . 5 . .<br>"
    + ". 5 1 5 .<br>"
    + "5 1 🀒 1 5<br>"
    + ". 5 1 5 .<br>"
    + ". . 5 . .<br>"
    + "reflected by KNIVES",
  "🀍": "HOOK<br>steal $2<br>in straight or diagonal line<br>reflected by HOOK",
  "🀨": "HARVESTER<br>gain $4<br>move forward 1",
  "🀗": "BACKSTABBER<br>pay $3<br>kill anything behind you",
  "🀙": "FIREBALL<br>pay $3<br>explode at target<br>direct hits reflected by FIREBALL",
  "👍": "ACCEPT",
  "🚩": "CHALLENGE"
}
const X2_TOOLTIPS = {
  "🀥": "2X FLOWER<br>gain $6<br>"
    + "move to an X:<br>"
    + "<br>"
    + "X X X X X<br>"
    + "X X X X X<br>"
    + "X X 🀥 X X<br>"
    + "X X X X X<br>"
    + "X X X X X<br>",
  "🀐": "2X BIRD<br>gain $4<br>"
    + "reveal 2 unused tiles<br>"
    + "move to an X:<br>"
    + "<br>"
    + ". . . . X . . . .<br>"
    + ". . . X X X . . .<br>"
    + ". . X X X X X . .<br>"
    + ". X X X X X X X .<br>"
    + "X X X X 🀛 X X X X<br>"
    + ". X X X X X X X .<br>"
    + ". . X X X X X . .<br>"
    + ". . . X X X . . .<br>"
    + ". . . . X . . . .",
  "🀛": "2X GRENADE <br>pay $3<br>"
    + "roll a grenade to the X if unobstructed and explode a 3x3 square twice:<br>"
    + "<br>"
    + ". . X . .<br>"
    + ". . . . .<br>"
    + "X . 🀛 . X<br>"
    + ". . . . .<br>"
    + ". . X . .",
  "🀒": "2X KNIVES<br>pay the amount shown to kill twice:<br>"
    + "<br>"
    + ". . 5 . .<br>"
    + ". 5 1 5 .<br>"
    + "5 1 🀒 1 5<br>"
    + ". 5 1 5 .<br>"
    + ". . 5 . .<br>"
    + "reflected twice by KNIVES",
  "🀍": "2X HOOK<br>steal $4<br>in straight or diagonal line<br>reflected twice by HOOK",
  "🀨": "2X HARVESTER<br>NOT IMPLEMENTED",
  "🀗": "2X BACKSTABBER<br>NOT IMPLEMENTED",
  "🀙": "2X FIREBALL<br>NOT IMPLEMENTED",
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
  X2_TOOLTIPS,
};

