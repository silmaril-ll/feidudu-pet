// 肥嘟嘟 desktop-pet frames. Every frame shares one canvas and one ground point,
// and every random texture is seeded, so frames line up and nothing flickers.
const PW = 560, PH = 260, OX = 136, GY = 230, PS = 2.2;
const PO = { lineS: 2.7, border: 9, minDot: 3, shadow: 0, shadowColor: 'rgba(0,0,0,0)' };

function frame(parts, warp, extra){
  extra = extra || {};
  const cv = ART.mk(extra.w || PW, extra.h || PH), ctx = cv.getContext('2d');
  if (extra.before) extra.before(ctx);
  const T = extra.T || { x: OX, y: GY, s: PS, r: 0 };
  ART.figure(ctx, parts, Object.assign({}, T, { warp: warp }), Object.assign({ seed: 91 }, PO));
  return cv.toDataURL('image/png');
}
// the real head's little smile turned into a pout (a bit unhappy, not scared)
function pout(parts){ return parts.map(p => p.line === 'M4.5,-5 Q7.5,-2.2 10.5,-5' ? Object.assign({}, p, { line: 'M5,-3.6 Q7.5,-5.8 10,-3.6' }) : p); }
// being petted: a wide contented smile and a pink blush on the real head
function content(parts){
  return parts.map(p => {
    if (p.line === 'M4.5,-5 Q7.5,-2.2 10.5,-5') return Object.assign({}, p, { line: 'M3.4,-6.2 Q7.5,-.4 11.6,-6.2', lw: 1.5 });
    if (p.blush) return Object.assign({}, p, { color: 'rgba(236,110,115,.85)' });     // the cheeks on the body go pinker too
    return p;
  }).concat([{ blush: [13, -9, 4.4, 2.9], color: 'rgba(236,105,110,.9)' }]);
}
// picked up by the middle of the back: curls into a loose C around a point below the body
const CURL = (R, a, psi) => p => {
  const xm = 66, yc = -27, d = yc - p[1];
  const th = (p[0] - xm) / R * (p[0] < xm ? 1 + a : 1 - a);
  const X = xm + (R + d) * Math.sin(th), Y = (yc + R) - (R + d) * Math.cos(th);
  const gx = xm, gy = -55, c = Math.cos(psi), s = Math.sin(psi);
  return [gx + (X - gx) * c - (Y - gy) * s, gy + (X - gx) * s + (Y - gy) * c];
};
const FOOT = [OX + 65 * PS, GY];            // ground contact point, the pivot for crawling/climbing
const gauss = (x, c, w) => Math.exp(-Math.pow((x - c) / w, 2));
const hgt = y => Math.max(0, Math.min(1, -y / 55));

const WARP = {
  crawl: t => p => { const c = 150 - t * 170, g = gauss(p[0], c, 15); return [p[0] - 1.6 * g, p[1] - 4.8 * g * (.55 + .45 * hgt(p[1]))]; },
  breathe: ph => p => { const k = Math.sin(ph); return [p[0] + (p[0] - 65) * -.006 * k, p[1] * (1 + .028 * k)]; },
  wiggle: ph => p => { const front = p[0] < 60 ? Math.pow(1 - p[0] / 60, 1.3) : 0, s = Math.sin(ph); return [p[0] + 5.5 * s * hgt(p[1]) + 2 * s * front, p[1] - 7 * Math.abs(s) * front + p[1] * .035 * Math.cos(2 * ph)]; },
  shake: dx => p => [p[0] + dx * (.4 + .6 * hgt(p[1])), p[1]],
  munch: ph => p => { const f = p[0] < 26 ? 1 - p[0] / 26 : 0; return [p[0] - 1.2 * f * Math.max(0, Math.sin(ph)), p[1] + 3 * f * Math.sin(ph)]; },
  // pulled by the head: the rear prolegs keep gripping, the front stretches out and thins
  tug: T => p => { const f = Math.pow(Math.max(0, 1 - p[0] / 118), 1.15), cy = -26; return [p[0] - 36 * T * f, cy + (p[1] - cy) * (1 - .2 * T * f) - 9 * T * f]; },
  sleep: ph => p => { const k = Math.sin(ph), f = p[0] < 28 ? 1 - p[0] / 28 : 0; return [p[0], p[1] * (1 + .016 * k) + 2.6 * f]; },
  // casting at an edge: the back prolegs hold on, the body curves up smoothly behind the saddle band and the
  // whole front half rears up, head nodding as it feels around for the next foothold
  wave: (th, nod) => {
    const lift = bend(90, 36, th, -1), head = bend(24, 12, nod, -1);
    // prolegs under the raised part tuck in a little instead of dangling
    const tuck = p => { if (p[1] < -4) return p; const t = Math.max(0, Math.min(1, (90 - p[0]) / 30)) * Math.min(1, th / .5); return [p[0], p[1] - 2.2 * t * t * (3 - 2 * t) * (p[1] + 4) / 7]; };
    return p => lift(head(tuck(p)));
  },
  // threat display ("snake pose"): the head tucks in, the thorax swells so the false eyes look huge,
  // and the whole front rears up high; sw sways it a little while holding the pose
  snake: (th, sw) => {
    const lift = bend(84, 30, th + sw, -1), tuck = bend(22, 10, -.55 * Math.min(1, th / .9), -1);
    const swell = p => { const cx = 32, cy = -37, d = Math.hypot(p[0] - cx, p[1] - cy), f = Math.max(0, 1 - d / 26), k = 1 + .24 * f * f * (3 - 2 * f) * Math.min(1, th / .9); return [cx + (p[0] - cx) * k, cy + (p[1] - cy) * k]; };
    const legs = p => { if (p[1] < -4) return p; const t = Math.max(0, Math.min(1, (84 - p[0]) / 30)); return [p[0], p[1] - 2.4 * t * t * (3 - 2 * t) * (p[1] + 4) / 7]; };
    return p => lift(tuck(swell(legs(p))));
  },
  // petted: melts a little flatter and longer, breathing slow and deep (the feet stay where they are)
  comfy: ph => p => { const k = Math.sin(ph); return [p[0] + (p[0] - 65) * (.035 + .006 * k), p[1] * (.9 + .02 * k)]; },
  // holding on while the window is dragged: pressed flat, legs spread, trembling
  cling: dx => p => [p[0] + (p[0] - 65) * .05 + dx * hgt(p[1]), p[1] * .8],
  // pushing out a frass pellet: the rear end curves up a little
  strain: k => bend(92, 24, .58 * k, 1)
};

// Bend the body smoothly instead of hinging it: starting at `hinge`, the centre line curves up by `theta`
// over `zone` units, then carries on straight. side -1 bends the front (x < hinge), +1 the rear.
// Every point keeps its distance from the centre line, so the outline, belly band and prolegs follow the curve.
function bend(hinge, zone, theta, side){
  const yc = -27, N = 90, du = 150 / N, table = [[hinge, yc, 0]];
  let x = hinge, y = yc;
  for (let i = 1; i <= N; i++) {
    const t = Math.min(1, i * du / zone), a = theta * t * t * (3 - 2 * t);
    x += side * Math.cos(a) * du; y -= Math.sin(a) * du;
    table.push([x, y, a]);
  }
  return p => {
    const u = side < 0 ? hinge - p[0] : p[0] - hinge;
    if (u <= 0 || theta === 0) return p;
    const k = Math.min(N, u / du), i = Math.floor(k), f = k - i, A = table[i], B = table[Math.min(N, i + 1)];
    const cx = A[0] + (B[0] - A[0]) * f, cy = A[1] + (B[1] - A[1]) * f, a = A[2] + (B[2] - A[2]) * f;
    const off = yc - p[1];                                   // how far above the centre line
    return [cx - side * Math.sin(a) * off, cy - Math.cos(a) * off];
  };
}

// a frass pellet: a little barrel with six grooves down its length, one end showing
// (drawn bigger than life so it's clickable)
function frassParts(){
  return [
    { d: 'M-5,-6.2 C-7,-3.4 -7,3.8 -5,6.8 C-2.8,8.4 2.8,8.4 5,6.8 C7,3.8 7,-3.4 5,-6.2 Z', fill: '#58663a', hatch: -1.3, lw: 1.3 },
    { line: 'M-3.3,-6.9 C-4.9,-2.6 -4.9,3.2 -3.3,7.5 M-1.1,-7.3 C-1.7,-2.6 -1.7,3.4 -1.1,7.9 M1.2,-7.3 C1.8,-2.6 1.8,3.4 1.2,7.9 M3.4,-6.9 C5,-2.6 5,3.2 3.4,7.5',
      lw: .8, color: '#37401f', double: false },
    { line: 'M-4.3,-3.6 C-4.8,-.8 -4.8,2.2 -4.2,4.8', lw: 1.3, color: 'rgba(205,214,160,.75)', double: false },
    { d: E(0, -6.3, 5, 1.9), fill: '#74834a', lw: 1.1 },
    { line: 'M0,-6.3 L-2.6,-7.4 M0,-6.3 L2.6,-7.4 M0,-6.3 L-3.2,-5.6 M0,-6.3 L3.2,-5.6 M0,-6.3 L0,-4.5', lw: .6, color: '#4b5629', double: false }
  ];
}

// the leaf being eaten, `stage` bites taken out of it; drawn as its own layer under the munching body
function leafBitten(ctx, stage, parts){
  if (stage > 3) return;
  const T = { x: OX - 4 * PS, y: GY - 7 * PS, s: PS * .56, r: Math.PI + .06 };
  const c = ART.mk(PW, PH), x = c.getContext('2d');
  ART.figure(x, parts, T, Object.assign({}, PO, { seed: 60, border: 6 }));
  x.save(); x.globalCompositeOperation = 'destination-out';
  const bites = [[6, -3], [24, -5], [42, -4]];
  for (let b = 0; b < stage; b++) {
    const n = ART.Noise(310 + b); x.beginPath();
    for (let k = 0; k <= 40; k++) {
      const a = k / 40 * Math.PI * 2, rr = 13 + (n.n2(Math.cos(a) * 3 + 5, Math.sin(a) * 3 + 5) - .5) * 6;
      const lx = bites[b][0] + Math.cos(a) * rr, ly = bites[b][1] + Math.sin(a) * rr;
      const cs = Math.cos(T.r), sn = Math.sin(T.r), px = T.x + (lx * cs - ly * sn) * T.s, py = T.y + (lx * sn + ly * cs) * T.s;
      k ? x.lineTo(px, py) : x.moveTo(px, py);
    }
    x.fill();
  }
  x.restore(); ctx.drawImage(c, 0, 0);
}

// a speech bubble; long text gets a wider canvas (the tail always sits in the middle of the canvas).
// English bubbles use the Patrick Hand font and are as wide as their text.
function bubble(text, w, en){
  if (en) { const m = ART.mk(10, 10).getContext('2d'); m.font = '32px "Patrick Hand"'; w = Math.max(104, Math.ceil(m.measureText(text).width) + 44); }
  const W = w || 120, CW = Math.max(200, W + 24), c = CW / 2;
  const cv = ART.mk(CW, 120), ctx = cv.getContext('2d');
  const x0 = c - W / 2, x1 = c + W / 2;
  const d = 'M' + (x0 + 16) + ',14 L' + (x1 - 16) + ',14 C' + x1 + ',14 ' + x1 + ',20 ' + x1 + ',34 L' + x1 + ',50 C' + x1 + ',64 ' + x1 + ',70 ' + (x1 - 16) + ',70 L' + (c + 14) + ',70 L' + (c + 2) + ',96 L' + (c - 8) + ',70 L' + (x0 + 16) + ',70 C' + x0 + ',70 ' + x0 + ',64 ' + x0 + ',50 L' + x0 + ',34 C' + x0 + ',20 ' + x0 + ',14 ' + (x0 + 16) + ',14 Z';
  ART.figure(ctx, [{ d: d, fill: '#fffdf6', hatchK: .25, step: 1, lw: 2 }], { x: 0, y: 0, s: 1, r: 0 }, Object.assign({}, PO, { seed: 70 + text.length, border: 6, lineS: 1.4 }));
  ctx.font = en ? '32px "Patrick Hand"' : '34px "Long Cang"'; ctx.fillStyle = '#3b2f29'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(text, c, 44);
  return cv.toDataURL('image/png');
}

// Every animation, drawn with the given parts. The body uses fatParts(); an accessory uses just its own parts,
// bent by exactly the same warps, so it becomes a layer that sits on the body in every frame.
function buildAnims(body, angry, overlay){
  const anims = {};
  const add = (name, frames, anchor, w, h) => { anims[name] = { frames: frames, anchor: anchor, w: w || PW, h: h || PH }; };
  const loop = (n, fn) => { const a = []; for (let i = 0; i < n; i++) a.push(fn(i)); return a; };
  add('crawl', loop(8, i => frame(body, WARP.crawl(i / 8))), FOOT);
  add('idle', loop(8, i => frame(body, WARP.breathe(i / 8 * Math.PI * 2))), FOOT);
  add('wiggle', loop(8, i => frame(body, WARP.wiggle(i / 8 * Math.PI * 2))), FOOT);
  add('angry', [-1.4, 1.4, 0].map(dx => frame(angry, WARP.shake(dx))), FOOT);
  add('sleep', loop(8, i => frame(body, WARP.sleep(i / 8 * Math.PI * 2))), FOOT);
  add('tug', [0, .2, .4, .6, .8, 1].map(T => frame(angry, WARP.tug(T))), [OX + 112 * PS, GY]);
  // casting: 3 frames rising (played backwards to lower), then 8 frames swaying around
  const wave = [.2, .42, .6].map(th => frame(body, WARP.wave(th, 0)));
  loop(8, i => { const ph = i / 8 * Math.PI * 2; return frame(body, WARP.wave(.62 + .14 * Math.sin(ph), .2 * Math.cos(ph))); }).forEach(f => wave.push(f));
  add('wave', wave, FOOT);
  // looking at the cursor: the front half raised to 9 angles, from level (0) to nearly upright (8); the program
  // picks whichever points the head at the cursor
  add('look', loop(9, i => frame(body, WARP.wave(i / 8 * 1.35, 0))), FOOT);
  add('comfy', loop(8, i => frame(content(body), WARP.comfy(i / 8 * Math.PI * 2))), FOOT);
  add('cling', [-1, 1, -.6, .6].map(dx => frame(pout(body), WARP.cling(dx))), FOOT);
  add('strain', [0, .35, .7, 1].map(k => frame(body, WARP.strain(k))), FOOT);
  // snake pose: 2 frames rearing up, then 4 frames holding it with a slow sway
  add('snake', [[.45, 0], [.8, 0], [.95, .04], [.95, 0], [.95, -.04], [.95, 0]].map(a => frame(angry, WARP.snake(a[0], a[1]))), FOOT);
  // munching: 6 chewing frames; the leaf itself is a separate layer (LEAVES in items.js, 4 bite stages each)
  add('munch', loop(6, i => frame(body, WARP.munch(i / 6 * Math.PI * 2))), FOOT);
  // lifted: pinched at the middle of the back, curled into a loose C, pouting (no horns: it's sulking, not scared)
  const PIN = [280, 50];
  add('lifted', loop(8, i => {
    const ph = i / 8 * Math.PI * 2, R = 45 + 8 * Math.sin(ph), a = .2 * Math.sin(ph + 1.2), psi = .12 * Math.sin(ph + .6);
    return frame(pout(body), CURL(R, a, psi), { T: { x: PIN[0] - 66 * PS, y: PIN[1] + 55 * PS, s: PS, r: 0 } });
  }), PIN);
  // hanging on silk from its mouth, head up, gently swaying; the mouth stays on the anchor
  const HW = 320, HH = 340, MOUTH = [160, 56];
  add('hang', loop(6, i => {
    const ph = i / 6 * Math.PI * 2, R = 120 + 30 * Math.sin(ph), r = Math.PI / 2 + .1 * Math.sin(ph);
    const m = CURL(R, 0, 0)([2, -6]), c = Math.cos(r), s = Math.sin(r);
    const T = { x: MOUTH[0] - (m[0] * c - m[1] * s) * PS, y: MOUTH[1] - (m[0] * s + m[1] * c) * PS, s: PS, r: r };
    return frame(body, CURL(R, 0, 0), { T: T, w: HW, h: HH });
  }), MOUTH, HW, HH);
  if (!overlay) {
    // 趴在窗口上沿后面往外偷看：正面的肥嘟嘟，边线以下的部分被窗口挡住，两只小脚扒着边
    // 前 3 帧是慢慢冒出来（倒着放是缩回去），后 6 帧是看着你、轻轻晃
    add('peek', [[.25, 0, 0], [.6, 0, 0], [.9, 0, 0]].concat(loop(6, i => { const ph = i / 6 * Math.PI * 2; return [1 + .03 * Math.sin(ph), 2 * Math.sin(ph + 1), 1]; }))
      .map(f => peekFrame(f[0], f[1], f[2])), FOOT);
    // 梦蝶：一小会儿的蛹（带蛹，腰上一圈丝、脚下一个丝垫），然后是蝴蝶（从上面看，翅膀一张一合）
    const pupa = pupaParts(C2.pupaG).concat([
      { line: 'M-11,-33 C-4,-30 5,-30 12,-33', lw: 1.3, color: '#fffdf5', double: false },
      { d: E(0, 1.5, 7, 2), fill: '#f4f1e6', outline: false }]);
    add('pupa', [-1.2, 1.2, 0, 0].map(dx => frame(pupa, p => [p[0] + dx * Math.min(1, -p[1] / 69), p[1]], { T: { x: FOOT[0], y: FOOT[1], s: PS * 1.1, r: 0 } })), FOOT);
    const FW = 340, FH = 250, MID = [170, 122];
    add('fly', [1, .78, .5, .28, .5, .78].map(k => frame(bfParts(), p => [p[0] * (Math.abs(p[0]) > 3 ? k : 1), p[1]], { T: { x: MID[0], y: MID[1], s: 2.6, r: 0 }, w: FW, h: FH })), MID, FW, FH);
  }
  return anims;
}

// the front-facing caterpillar hiding behind the edge (ground line) and peeking over it; rise 1 shows it down to
// just under the false eyes; `hands` 1 draws the two little feet gripping the edge
function peekFrame(rise, dx, hands){
  const s = PS * .8, cv = ART.mk(PW, PH), ctx = cv.getContext('2d'), body = ART.mk(PW, PH);
  ART.figure(body.getContext('2d'), fatFront(), { x: FOOT[0] + dx, y: GY + (34 + (1 - rise) * 70) * s, s: s, r: 0 }, Object.assign({ seed: 91 }, PO));
  ctx.drawImage(body, 0, 0, PW, GY, 0, 0, PW, GY);          // below the edge it's behind the window
  if (hands) ART.figure(ctx, [-27, 27].map(x => ({ d: E(x, -2.4, 5.2, 3.6), fill: '#b5d98a', lw: 1.3 })),
    { x: FOOT[0] + dx, y: GY, s: s, r: 0 }, Object.assign({ seed: 92 }, PO, { border: 4 }));
  return cv.toDataURL('image/png');
}

// 礼花筒（每吃满一百片叶子的庆祝）：一个斜条纹的纸筒，口朝上，口上一圈金边，底下拖一根拉线。
// 筒尖在 (0,0)，筒口中间在 (0,-34)；程序把筒尖放在地上、按方向斜着立起来，彩纸从筒口喷出去
function popperParts(){
  const P = [];
  P.push({ line: 'M0,0 C3,5 -3,9 1,14 C4,17 2,20 0,22', lw: 1.3, color: '#c9a25a', double: false });      // 拉线
  P.push({ d: 'M-14,-33 L14,-33 L2.2,-.5 C1,.6 -1,.6 -2.2,-.5 Z', fill: '#f4b8c8', hatch: -1.1 });
  P.push({ line: 'M-11.5,-26 L8,-33 M-9.5,-18 L11.8,-26 M-7,-10 L9,-17 M-4.5,-3.5 L5.6,-8', lw: 3.2, color: '#f7d774', double: false });
  P.push({ d: ART.E(0, -33, 14.5, 3.6), fill: '#f3d36b', lw: 1.2 });
  P.push({ d: ART.E(0, -33.4, 10.5, 2), fill: '#7a5a3a', outline: false });
  return P;
}
function popperPic(){
  const c = ART.mk(120, 180);
  ART.figure(c.getContext('2d'), popperParts(), { x: 60, y: 120, s: 2.4, r: 0 }, Object.assign({}, PO, { seed: 230, border: 6, lineS: 2 }));
  return c.toDataURL('image/png');
}
// 彩纸：小方片、小圆片、小三角，还有卷卷的彩带，蜡笔画的，程序里一片片飞出来
const CONFETTI_COLORS = ['#f2a7b5', '#f7d774', '#9fd3e6', '#b8e0a0', '#c9b3ea', '#f5b87a'];
function confettiPics(){
  const shapes = [ 'M-4,-2.6 L4,-2.6 L4,2.6 L-4,2.6 Z', ART.E(0, 0, 3.2), 'M0,-3.6 L3.6,3 L-3.6,3 Z' ];
  const out = [];
  CONFETTI_COLORS.forEach((col, i) => shapes.forEach((d, k) => {
    const c = ART.mk(40, 40);
    ART.figure(c.getContext('2d'), [{ d: d, fill: col, lw: .8, hatchK: .4 }], { x: 20, y: 20, s: 2.4, r: (i + k) * .7 },
      Object.assign({}, PO, { seed: 240 + i * 3 + k, border: 2, lineS: 1 }));
    out.push(c.toDataURL('image/png'));
  }));
  CONFETTI_COLORS.forEach((col, i) => {                         // 卷卷的彩带
    const c = ART.mk(70, 70);
    ART.figure(c.getContext('2d'), [{ line: 'M-12,-8 C-6,-14 -2,-2 3,-6 C8,-10 10,2 14,-2 C16,-4 14,6 10,9', lw: 2.2, color: col, double: false }],
      { x: 35, y: 35, s: 2, r: i * 1.1 }, Object.assign({}, PO, { seed: 260 + i, cut: false, lineS: 1.4 }));
    out.push(c.toDataURL('image/png'));
  });
  return out;
}

function sparkle(col, s){
  const c = ART.mk(48, 48);
  ART.figure(c.getContext('2d'), [{ d: 'M0,-8 C1,-2.2 2.2,-1 8,0 C2.2,1 1,2.2 0,8 C-1,2.2 -2.2,1 -8,0 C-2.2,-1 -1,-2.2 0,-8 Z', fill: col, lw: 1, hatchK: .4 }],
    { x: 24, y: 24, s: s, r: 0 }, Object.assign({}, PO, { seed: 97, border: 3, lineS: 1.2 }));
  return c.toDataURL('image/png');
}

// 泡泡的英文版（config 里 LANGUAGE = "en" 时用）；叶子的泡泡用 items.js 里的 en 名字
const BUBBLES_EN = {
  hum: 'Hmph!', niu: 'Wiggle~', zz: 'Zz…', burp: 'Burp~', yum: 'Yum!', dots: '...', hi: 'Morning!', nope: 'Nope!', aah: 'Waah~',
  zip: 'Zip~', heave: 'Hup!', hmm: 'Hm?', pu: 'Pff', back: "I'm back", pretty: 'Pretty?', tingly: 'Tingly~', shiny: 'Sparkly!',
  sleepy: 'Sleepy…', dream: 'I had a dream…', full: 'So full~', stuffed: "I'm stuffed", hiss: 'Hsss—!', hello: 'Hello!',
  sour: 'Sour!', asleep: 'Shh~ sleeping', fragrant: 'Smells nice~', picky: 'No way!', rutaceae: 'Citrus family only!',
  take_away: 'Take it away!', better: 'Much better', morning: 'Morning!', noon: 'Lunchtime!', afternoon: 'Afternoon!',
  evening: 'Evening!', late: "It's late…", welcome: "You're back!", reach: "Can't reach~", startle: 'Eek!', done: 'All done?',
  rest: 'Take a break?', busy: 'Whatcha doing?', comfy: 'Comfy~', phew: 'Phew~'
};

async function renderPet(){
  const f = new FontFace('Long Cang', 'url(LongCang.ttf)'); await f.load(); document.fonts.add(f);
  const f2 = new FontFace('Patrick Hand', 'url(PatrickHand.ttf)'); await f2.load(); document.fonts.add(f2);
  ART.initTooth(PW, 460, 5);
  const out = { scale: 2, anims: buildAnims(fatParts(), fatParts({ horns: true })), bubbles: {}, bubbles_en: {}, accessories: {}, leaves: {}, shop: { gacha_price: GACHA_PRICE } };
  const bubbles = [['hum', '哼！', 104], ['niu', '扭扭～', 134], ['zz', 'Zz…', 110], ['burp', '嗝～', 104], ['yum', '好吃！', 128], ['dots', '……', 104], ['hi', '早呀', 110],
   ['nope', '不放！', 118], ['aah', '哇啊～', 118], ['zip', '咻～', 104], ['heave', '嘿咻', 110],
   ['hmm', '嗯？', 104], ['pu', '噗', 104], ['back', '回来啦', 134],
   ['pretty', '好看吗？', 150], ['tingly', '麻麻的～', 150], ['shiny', '亮晶晶！', 150], ['sleepy', '困了…', 118], ['dream', '做了个梦…', 176], ['full', '好撑～', 134],
   ['stuffed', '吃不下了', 150], ['hiss', '嘶——！', 134],
   ['hello', '你好呀', 134], ['sour', '酸！', 104], ['asleep', '嘘～睡着呢', 186], ['fragrant', '香香的～', 150], ['picky', '才不吃！', 150], ['rutaceae', '我只吃芸香科！', 256], ['take_away', '拿走！', 118], ['better', '这才对嘛', 150], ['morning', '早呀', 110], ['noon', '中午好', 134], ['afternoon', '下午好', 134],
   ['welcome', '你回来啦', 160], ['reach', '够不着～', 160], ['done', '忙完啦？', 160], ['rest', '歇一下？', 160], ['busy', '忙什么呢？', 186], ['startle', '吓！', 104], ['comfy', '舒服～', 134], ['phew', '呼～', 104],
   ['evening', '晚上好', 134], ['late', '夜深啦', 134]];
  // 饰品：每个动作一层，和身体用同样的弯法
  Object.keys(ACCESSORIES).forEach(name => {
    const a = ACCESSORIES[name], parts = a.parts();
    const anims = buildAnims(parts, parts, true);
    out.accessories[name] = { label: a.label, label_en: a.en || a.label, price: a.price, anims: Object.keys(anims).reduce((o, k) => (o[k] = anims[k].frames, o), {}) };
  });
  // 叶子：4 个咬了几口的样子；抽到时冒一个写着名字的泡泡
  Object.keys(LEAVES).forEach(name => {
    const l = LEAVES[name], parts = l.parts();
    const frames = [0, 1, 2, 3].map(stage => { const c = ART.mk(PW, PH); leafBitten(c.getContext('2d'), stage, parts); return c.toDataURL('image/png'); });
    out.leaves[name] = { label: l.label, label_en: l.en || l.label, weight: l.weight || 0, effect: l.effect || null, minutes: l.minutes || 0, frames: frames };
    bubbles.push(['leaf_' + name, l.label + '！', Math.min(190, 60 + 34 * l.label.length)]);
    out.bubbles_en['leaf_' + name] = bubble((l.en || l.label) + '!', 0, true);
  });
  out.sparkles = [sparkle('#f6d86b', 1.7), sparkle('#fff6c8', 1.3), sparkle('#fbe7a0', 1)];
  out.scents = [.9, 1.1, 1.3].map((k, i) => {               // 芸香叶：身边飘起来的一缕缕香味
    const c = ART.mk(40, 56);
    ART.figure(c.getContext('2d'), [{ line: 'M0,20 C-5,14 5,8 0,2 C-5,-4 5,-10 0,-16', lw: 1.6, color: ['#9cc3b4', '#b9d6c9', '#a9c8e0'][i], double: false }],
      { x: 20, y: 28, s: k, r: 0 }, Object.assign({}, PO, { seed: 220 + i, cut: false, lineS: 1.2 }));
    return c.toDataURL('image/png');
  });
  // 吃满一百片的庆祝泡泡：第100片！…第3000片！，再往后都是“又一百片！”
  for (let n = 100; n <= 3000; n += 100) { bubbles.push(['leaves_' + n, '第' + n + '片！', 44 + 24 * ('第' + n + '片！').length]); BUBBLES_EN['leaves_' + n] = 'Leaf #' + n + '!'; }
  bubbles.push(['leaves_more', '又一百片！', 190]); BUBBLES_EN.leaves_more = 'Another hundred!';
  bubbles.push(['hooray', '撒花～', 134]); BUBBLES_EN.hooray = 'Hooray!';
  out.popper = popperPic();
  out.confetti = confettiPics();
  bubbles.forEach(b => { out.bubbles[b[0]] = bubble(b[1], b[2]); });
  Object.keys(BUBBLES_EN).forEach(k => { out.bubbles_en[k] = bubble(BUBBLES_EN[k], 0, true); });
  const missing = bubbles.map(b => b[0]).filter(k => !out.bubbles_en[k]);
  if (missing.length) throw new Error('BUBBLES_EN 少了：' + missing.join(', '));
  const fc = ART.mk(64, 64);
  ART.figure(fc.getContext('2d'), frassParts(), { x: 32, y: 31, s: PS, r: -.3 }, Object.assign({}, PO, { seed: 95, border: 5 }));
  out.frass = fc.toDataURL('image/png');
  out.skin = renderSkin();
  out.menu = renderMenu();
  const ic = ART.mk(256, 256), ix = ic.getContext('2d');
  ART.figure(ix, fatFront(), { x: 128, y: 128 + 48 * 2.1, s: 2.1, r: 0 }, Object.assign({}, PO, { seed: 93, border: 7, lineS: 2.6 }));
  out.icon = ic.toDataURL('image/png');
  return out;
}
