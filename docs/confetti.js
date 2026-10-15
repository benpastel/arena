// A burst of confetti over the whole page, falling and fading out on its own.

const PIECES = 140;
const MS = 2800;

function confetti(colors) {
  const canvas = document.createElement("canvas");
  canvas.className = "confetti";
  const ratio = window.devicePixelRatio || 1;
  canvas.width = window.innerWidth * ratio;
  canvas.height = window.innerHeight * ratio;
  document.body.append(canvas);
  const context = canvas.getContext("2d");
  context.scale(ratio, ratio);

  // thrown up from across the bottom third, then falling and fluttering
  const pieces = Array.from({length: PIECES}, () => ({
    x: Math.random() * window.innerWidth,
    y: window.innerHeight * (0.7 + Math.random() * 0.4),
    vx: (Math.random() - 0.5) * 5,
    vy: -(9 + Math.random() * 9),
    spin: Math.random() * Math.PI,
    spinSpeed: (Math.random() - 0.5) * 0.3,
    width: 5 + Math.random() * 5,
    height: 8 + Math.random() * 6,
    color: colors[Math.floor(Math.random() * colors.length)],
  }));

  const start = performance.now();
  let last = start;
  function frame(now) {
    const step = Math.min(2, (now - last) / 16);
    last = now;
    const age = (now - start) / MS;
    context.clearRect(0, 0, window.innerWidth, window.innerHeight);
    context.globalAlpha = Math.max(0, 1 - Math.max(0, age - 0.6) / 0.4);
    for (const piece of pieces) {
      piece.vy += 0.32 * step;
      piece.vx *= 0.99;
      piece.x += piece.vx * step;
      piece.y += Math.min(piece.vy, 6) * step;
      piece.spin += piece.spinSpeed * step;
      context.save();
      context.translate(piece.x, piece.y);
      context.rotate(piece.spin);
      // the flutter: a piece narrows and widens as it turns
      context.scale(Math.cos(piece.spin * 2), 1);
      context.fillStyle = piece.color;
      context.fillRect(-piece.width / 2, -piece.height / 2, piece.width, piece.height);
      context.restore();
    }
    if (age < 1) {
      window.requestAnimationFrame(frame);
    } else {
      canvas.remove();
    }
  }
  window.requestAnimationFrame(frame);
}

export {confetti};
