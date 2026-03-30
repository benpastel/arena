"use strict";

// must match python state and CSS sizing assumptions
const ROWS = 5;
const COLUMNS = 5;

// must match css classes and python enums
const NORTH_PLAYER = "north";
const SOUTH_PLAYER = "south";
const SOLO_MODE = "solo";
const PLAYERS = [NORTH_PLAYER, SOUTH_PLAYER];

// must match css classes
const HIGHLIGHT = "highlight"; // squares, actions, or tiles the player can select right now
const CHOSEN_START = "chosen-start"; // the square of the tile selected mid-turn
const CHOSEN_ACTION = "chosen-action"; // an action is selected mid-turn
const CHOSEN_TARGET = "chosen-target"; // a square is selected mid-turn as the target

const TILES = {
  "🀥": "🀥", // flower
  "🀐": "🀐", // bird
  "🀛": "🀛", // grenades
  "🀒": "🀒", // knives
  "🀍": "🀍", // hook
  "🀨": "🀨", // harvester
  "🀗": "🀗", // spider
  "🀇": "🀇", // backstabber
  "🀙": "🀙", // fireball
  "🀩": "🀩", // trickster
  "🀎": "🀎", // ram
  "🀌": "🀌", // thief
};
const HIDDEN_TILE = "🀫";
const OTHER_ACTIONS = {
  "↕": "↕", // move
};
const RESPONSES = {
  "👍": "👍", // accept
  "🚩": "🚩", // challenge
};

const TOOLTIPS = {
  "↕": "MOVE<br>move 1<br>gain $1",
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
    + "X X 🀐 X X<br>"
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
  "🀇": "BACKSTABBER<br>pay $3, kill behind you<br>reflected by BACKSTABBER<br>"
    + "OR<br>"
    + "move 2, gain $1",
  "🀙": "FIREBALL<br>pay $3<br>explode at target<br>direct hits reflected by FIREBALL",
  "🀩": "TRICKSTER<br>gain $1<br>move knight-like<br>if you land on an enemy, switch identities<br>and bump them to a random adjacent unoccupied square",
  "🀎": "RAM<br>pay $3, move 1 cardinal<br>"
    + "then knockback: all tiles adjacent to where you end up get pushed back 1<br>"
    + "or die if they can't move<br>"
    + "<br>"
    + "↖ ↑ ↗<br>"
    + "← 🀎 →<br>"
    + "↙ ↓ ↘<br>",
  "🀌": "THIEF<br>steal $4<br>swap places with target<br>reflected by THIEF<br>"
    + "x x x<br>"
    + "x 🀌 x<br>"
    + "x x x<br>"
    + "<br>reflected by THIEF",
  "🀗": "SPIDER<br>move 2, gain $0<br>after exchange, gain a turn<br>"
    + "lays webs<br>"
    + "enemy crossing web loses a turn<br>"
    + "webs block fireballs<br>"
    + "fireballs & grenades destroy webs",
  "👍": "ACCEPT",
  "🚩": "CHALLENGE"
}

export {
  ROWS,
  COLUMNS,
  NORTH_PLAYER,
  SOUTH_PLAYER,
  SOLO_MODE,
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

