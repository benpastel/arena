// Animates the change from one state to the next, so it's easier to see what happened:
// a piece slides to its new square, a dying tile flies to the graveyard, and a tile
// placed from a hand flies onto the board.
//
// Call snapshot() before drawing the new state, and animate() after, with the new state.

import {PLAYERS} from "./constants.js";
import {findCell} from "./renderState.js";

const SLIDE_MS = 220;
const DIE_MS = 450;
const PLACE_MS = 300;

let lastView = null;

// where everything was drawn before the new state replaces it
function snapshot(board) {
  if (!lastView) {
    return null;
  }
  const pieces = {};
  const hands = {};
  for (const player of PLAYERS) {
    pieces[player] = lastView.positions[player].map(([row, col], index) => {
      const cell = findCell(board, row, col);
      const piece = cell && cell.querySelector(".piece");
      if (!piece) {
        return null;
      }
      const style = getComputedStyle(piece);
      return {
        rect: piece.getBoundingClientRect(),
        glyph: lastView.tiles_on_board[player][index],
        color: style.color,
        fontSize: style.fontSize,
      };
    });
    hands[player] = Array.from(
      document.querySelectorAll(`.strip.${player} .hand-tile`),
      (tile) => ({glyph: tile.textContent, rect: tile.getBoundingClientRect()}),
    );
  }
  return {view: lastView, pieces, hands};
}

function animate(before, board, view) {
  const previous = lastView;
  lastView = view;
  if (!before || before.view !== previous) {
    return;
  }

  // a new game deals new hands and empties the graveyard: nothing to animate
  const was = before.view;
  if (
    view.discard.length < was.discard.length ||
    PLAYERS.some((p) => view.tiles_in_hand[p].length > was.tiles_in_hand[p].length)
  ) {
    return;
  }

  const slides = [];
  const deaths = [];
  const placements = [];
  for (const player of PLAYERS) {
    const placed = was.tiles_in_hand[player].length - view.tiles_in_hand[player].length;
    const change = diff(was.positions[player], view.positions[player], placed);
    if (!change) {
      continue;
    }
    for (const [from, to] of change.moved) {
      slides.push([before.pieces[player][from], view.positions[player][to]]);
    }
    for (const index of change.died) {
      deaths.push(before.pieces[player][index]);
    }
    for (const index of change.appended) {
      placements.push([player, index]);
    }
  }
  if (slides.length + deaths.length + placements.length > 6) {
    return;
  }

  for (const [from, [row, col]] of slides) {
    const piece = pieceAt(board, row, col);
    if (from && piece) {
      fly(piece, from.rect, SLIDE_MS);
    }
  }

  // the dead are the newest tiles in the graveyard
  const graves = Array.from(document.querySelectorAll(".graveyard-contents .acc-tile"));
  const newGraves = graves.slice(was.discard.length);
  deaths.forEach((from, i) => {
    if (from) {
      ghostToGrave(from, newGraves[i]);
    }
  });

  // a placed tile leaves after any tile it replaces
  const delay = deaths.length ? DIE_MS / 3 : 0;
  for (const [player, index] of placements) {
    const [row, col] = view.positions[player][index];
    const piece = pieceAt(board, row, col);
    const glyph = view.tiles_on_board[player][index];
    const hand = before.hands[player];
    const from = hand.find((t) => t.glyph === glyph) || hand[hand.length - 1];
    if (piece && from) {
      fly(piece, from.rect, PLACE_MS, delay);
    }
  }
}

// How one player's pieces changed, given how the server changes its list of positions:
// a move changes a position in place, a death removes it, and a tile placed from the
// hand is appended. Returns the indexes that moved (old to new), died (old), and were
// appended (new), choosing which died so the fewest pieces moved.
function diff(was, now, placed) {
  const died = was.length - now.length + placed;
  if (placed < 0 || died < 0 || died > was.length) {
    return null;
  }
  const same = (a, b) => a[0] === b[0] && a[1] === b[1];
  let best = null;
  for (const removed of combinations(was.length, died)) {
    const kept = was.map((_, i) => i).filter((i) => !removed.includes(i));
    const moved = kept
      .map((oldIndex, newIndex) => [oldIndex, newIndex])
      .filter(([oldIndex, newIndex]) => !same(was[oldIndex], now[newIndex]));
    if (!best || moved.length < best.moved.length) {
      best = {moved, died: removed, appended: now.map((_, i) => i).slice(kept.length)};
    }
  }
  return best;
}

function combinations(n, k, start = 0) {
  if (k === 0) {
    return [[]];
  }
  const result = [];
  for (let i = start; i <= n - k; i++) {
    for (const rest of combinations(n, k - 1, i + 1)) {
      result.push([i, ...rest]);
    }
  }
  return result;
}

function pieceAt(board, row, col) {
  const cell = findCell(board, row, col);
  return cell && cell.querySelector(".piece");
}

// draw an element at its new place as if it were still at the old rect, then let it go
function fly(element, fromRect, duration, delay = 0) {
  const to = element.getBoundingClientRect();
  const dx = fromRect.left + fromRect.width / 2 - (to.left + to.width / 2);
  const dy = fromRect.top + fromRect.height / 2 - (to.top + to.height / 2);
  const scale = fromRect.height / to.height;
  // above the squares it passes over
  element.style.zIndex = 3;
  element
    .animate(
      [{transform: `translate(${dx}px, ${dy}px) scale(${scale})`}, {transform: "none"}],
      {duration, delay, easing: "ease-out", fill: "backwards"},
    )
    .finished.then(() => element.style.removeProperty("z-index"), () => {});
}

// a copy of the dead tile, which pauses where it died, then flies to its place in the graveyard
function ghostToGrave(from, grave) {
  const ghost = document.createElement("span");
  ghost.className = "ghost";
  ghost.textContent = grave ? grave.textContent : from.glyph;
  ghost.style.left = `${from.rect.left}px`;
  ghost.style.top = `${from.rect.top}px`;
  ghost.style.fontSize = from.fontSize;
  ghost.style.color = from.color;
  document.body.append(ghost);

  const keyframes = [{transform: "none", opacity: 1}, {transform: "none", opacity: 1, offset: 0.25}];
  if (grave) {
    const to = grave.getBoundingClientRect();
    const dx = to.left + to.width / 2 - (from.rect.left + from.rect.width / 2);
    const dy = to.top + to.height / 2 - (from.rect.top + from.rect.height / 2);
    keyframes.push({transform: `translate(${dx}px, ${dy}px) scale(${to.height / from.rect.height})`, opacity: 0.6});
    grave.animate([{opacity: 0}, {opacity: 0}], {duration: DIE_MS});
  } else {
    keyframes.push({transform: "scale(0.6)", opacity: 0});
  }
  ghost
    .animate(keyframes, {duration: DIE_MS, easing: "ease-in"})
    .finished.then(() => ghost.remove(), () => ghost.remove());
}

export {snapshot, animate};
