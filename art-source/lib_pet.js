// Crayon + torn-paper renderer. Every random effect is seeded, so the same page always renders identically.
const ART = (function(){
  function rng(seed){ let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function Noise(seed){
    const r = rng(seed), P = new Uint16Array(512), p = [];
    for (let i = 0; i < 256; i++) p[i] = i;
    for (let i = 255; i > 0; i--) { const j = Math.floor(r() * (i + 1)); const t = p[i]; p[i] = p[j]; p[j] = t; }
    for (let i = 0; i < 512; i++) P[i] = p[i & 255];
    const V = new Float32Array(256); for (let i = 0; i < 256; i++) V[i] = r();
    const fade = t => t * t * (3 - 2 * t);
    function n2(x, y){
      const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
      const X = xi & 255, Y = yi & 255, X1 = (X + 1) & 255, Y1 = (Y + 1) & 255;
      const a = V[P[X + P[Y]]], b = V[P[X1 + P[Y]]], c = V[P[X + P[Y1]]], d = V[P[X1 + P[Y1]]];
      const u = fade(xf), v = fade(yf);
      return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
    }
    function fbm(x, y, o){ o = o || 3; let s = 0, amp = .5, f = 1, nm = 0; for (let i = 0; i < o; i++) { s += amp * n2(x * f, y * f); nm += amp; amp *= .5; f *= 2.03; } return s / nm; }
    return { n2, fbm };
  }
  const N = Noise(11); let G = 1; function setGrain(g){ G = g; }
  function mk(w, h){ const c = document.createElement('canvas'); c.width = Math.max(1, Math.ceil(w)); c.height = Math.max(1, Math.ceil(h)); return c; }
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;

  // ---------- color ----------
  function hex2rgb(h){ h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
  function rgb2hsl(r, g, b){ r /= 255; g /= 255; b /= 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b); let h = 0, s = 0; const l = (mx + mn) / 2; if (mx !== mn) { const d = mx - mn; s = l > .5 ? d / (2 - mx - mn) : d / (mx + mn); h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h /= 6; } return [h, s, l]; }
  function hsl2rgb(h, s, l){ if (s === 0) return [l * 255, l * 255, l * 255]; const f = (p, q, t) => { if (t < 0) t += 1; if (t > 1) t -= 1; if (t < 1 / 6) return p + (q - p) * 6 * t; if (t < 1 / 2) return q; if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6; return p; }; const q = l < .5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q; return [f(p, q, h + 1 / 3) * 255, f(p, q, h) * 255, f(p, q, h - 1 / 3) * 255]; }
  function shade(hex, dl, ds){ const c = hex2rgb(hex); let hsl = rgb2hsl(c[0], c[1], c[2]); const o = hsl2rgb(hsl[0], clamp(hsl[1] + (ds || 0), 0, 1), clamp(hsl[2] + dl, 0, 1)); return 'rgb(' + (o[0] | 0) + ',' + (o[1] | 0) + ',' + (o[2] | 0) + ')'; }

  // ---------- geometry ----------
  function E(cx, cy, rx, ry){ const k = .5523; ry = ry == null ? rx : ry; return 'M' + (cx - rx) + ',' + cy + ' C' + (cx - rx) + ',' + (cy - ry * k) + ' ' + (cx - rx * k) + ',' + (cy - ry) + ' ' + cx + ',' + (cy - ry) + ' C' + (cx + rx * k) + ',' + (cy - ry) + ' ' + (cx + rx) + ',' + (cy - ry * k) + ' ' + (cx + rx) + ',' + cy + ' C' + (cx + rx) + ',' + (cy + ry * k) + ' ' + (cx + rx * k) + ',' + (cy + ry) + ' ' + cx + ',' + (cy + ry) + ' C' + (cx - rx * k) + ',' + (cy + ry) + ' ' + (cx - rx) + ',' + (cy + ry * k) + ' ' + (cx - rx) + ',' + cy + ' Z'; }
  // a bent limb (finger, arm) as a closed outline around a polyline
  function limb(pts, w){
    const L = [], Rr = [], n = pts.length, h = w / 2;
    for (let i = 0; i < n; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
      let nx = -(b[1] - a[1]), ny = b[0] - a[0]; const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
      L.push([pts[i][0] + nx * h, pts[i][1] + ny * h]); Rr.push([pts[i][0] - nx * h, pts[i][1] - ny * h]);
    }
    const tip = pts[n - 1], pre = pts[n - 2], ang = Math.atan2(tip[1] - pre[1], tip[0] - pre[0]);
    let d = 'M' + L[0][0].toFixed(2) + ',' + L[0][1].toFixed(2);
    for (let i = 1; i < n; i++) d += ' L' + L[i][0].toFixed(2) + ',' + L[i][1].toFixed(2);
    for (let k = 1; k < 8; k++) { const a = ang + Math.PI / 2 - k / 8 * Math.PI; d += ' L' + (tip[0] + Math.cos(a) * h).toFixed(2) + ',' + (tip[1] + Math.sin(a) * h).toFixed(2); }
    for (let i = n - 1; i >= 0; i--) d += ' L' + Rr[i][0].toFixed(2) + ',' + Rr[i][1].toFixed(2);
    return d + ' Z';
  }
  function sample(d, step){
    const tk = d.match(/[MLCQZ]|-?\d*\.?\d+(?:e[-+]?\d+)?/gi); let i = 0, cur = null, x = 0, y = 0, sx = 0, sy = 0, cmd = 'M';
    const out = [], num = () => parseFloat(tk[i++]);
    while (i < tk.length) {
      if (/^[MLCQZ]$/i.test(tk[i])) cmd = tk[i++].toUpperCase();
      if (cmd === 'M') { x = num(); y = num(); sx = x; sy = y; cur = { pts: [[x, y]], closed: false }; out.push(cur); cmd = 'L'; }
      else if (cmd === 'L') { const nx = num(), ny = num(), n = Math.max(1, Math.ceil(Math.hypot(nx - x, ny - y) / step)); for (let k = 1; k <= n; k++) cur.pts.push([x + (nx - x) * k / n, y + (ny - y) * k / n]); x = nx; y = ny; }
      else if (cmd === 'C') { const a = [num(), num(), num(), num(), num(), num()]; const L = Math.hypot(a[0] - x, a[1] - y) + Math.hypot(a[2] - a[0], a[3] - a[1]) + Math.hypot(a[4] - a[2], a[5] - a[3]); const n = Math.max(2, Math.ceil(L / step)); for (let k = 1; k <= n; k++) { const t = k / n, m = 1 - t; cur.pts.push([m * m * m * x + 3 * m * m * t * a[0] + 3 * m * t * t * a[2] + t * t * t * a[4], m * m * m * y + 3 * m * m * t * a[1] + 3 * m * t * t * a[3] + t * t * t * a[5]]); } x = a[4]; y = a[5]; }
      else if (cmd === 'Q') { const a = [num(), num(), num(), num()]; const L = Math.hypot(a[0] - x, a[1] - y) + Math.hypot(a[2] - a[0], a[3] - a[1]); const n = Math.max(2, Math.ceil(L / step)); for (let k = 1; k <= n; k++) { const t = k / n, m = 1 - t; cur.pts.push([m * m * x + 2 * m * t * a[0] + t * t * a[2], m * m * y + 2 * m * t * a[1] + t * t * a[3]]); } x = a[2]; y = a[3]; }
      else if (cmd === 'Z') { cur.closed = true; if (cur.pts.length > 1) { const f = cur.pts[0], l = cur.pts[cur.pts.length - 1]; if (Math.hypot(f[0] - l[0], f[1] - l[1]) < 1e-6) cur.pts.pop(); } x = sx; y = sy; cmd = 'M'; if (i < tk.length && !/^[MLCQZ]$/i.test(tk[i])) i++; }
    }
    return out;
  }
  function xf(pts, T){ const c = Math.cos(T.r || 0), s = Math.sin(T.r || 0); return pts.map(p => [T.x + (p[0] * c - p[1] * s) * T.s, T.y + (p[0] * s + p[1] * c) * T.s]); }
  function wob(pts, closed, amp, freq, seed){
    const n = pts.length;
    return pts.map((p, i) => {
      const a = pts[closed ? (i - 1 + n) % n : Math.max(0, i - 1)], b = pts[closed ? (i + 1) % n : Math.min(n - 1, i + 1)];
      let nx = -(b[1] - a[1]), ny = b[0] - a[0]; const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
      const v = (N.fbm(p[0] * freq / G + seed * 13.1, p[1] * freq / G + seed * 7.7, 3) - .5) * 2 * amp;
      return [p[0] + nx * v, p[1] + ny * v];
    });
  }
  function bbox(list, pad){ let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; list.forEach(pts => pts.forEach(p => { if (p[0] < x0) x0 = p[0]; if (p[1] < y0) y0 = p[1]; if (p[0] > x1) x1 = p[0]; if (p[1] > y1) y1 = p[1]; })); pad = pad || 0; x0 = Math.floor(x0 - pad); y0 = Math.floor(y0 - pad); return { x: x0, y: y0, w: Math.ceil(x1 + pad - x0), h: Math.ceil(y1 + pad - y0) }; }
  function poly(x, pts, closed){ x.beginPath(); x.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) x.lineTo(pts[i][0], pts[i][1]); if (closed) x.closePath(); }

  // ---------- paper tooth (shared, fixed seed, aligned to the page) ----------
  let TOOTH = null;
  function initTooth(w, h, seed){
    const c = mk(w, h), x = c.getContext('2d'), im = x.createImageData(w, h), d = im.data, nz = Noise(seed || 5);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const v = nz.n2(i / (1.6 * G), j / (1.6 * G)) * .55 + nz.n2(i / (6 * G) + 50, j / (6 * G) + 50) * .3 + nz.n2(i / (38 * G) + 90, j / (38 * G)) * .15;
      const a = clamp((v - .5) / .2, 0, 1), k = (j * w + i) * 4; d[k + 3] = a * 255;
    }
    x.putImageData(im, 0, 0); TOOTH = c; return c;
  }
  function erode(x, b, amt){ if (!TOOTH || amt <= 0) return; x.save(); x.globalCompositeOperation = 'destination-out'; x.globalAlpha = amt; x.drawImage(TOOTH, b.x, b.y, b.w, b.h, b.x, b.y, b.w, b.h); x.restore(); }

  // ---------- paper background ----------
  function paper(ctx, w, h, base, seed){
    ctx.fillStyle = base; ctx.fillRect(0, 0, w, h);
    const im = ctx.getImageData(0, 0, w, h), d = im.data, nz = Noise(seed || 21);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const v = (nz.fbm(i / 90, j / 90, 3) - .5) * 14 + (nz.n2(i / 2.2, j / 2.2) - .5) * 9;
      const k = (j * w + i) * 4; d[k] = clamp(d[k] + v, 0, 255); d[k + 1] = clamp(d[k + 1] + v, 0, 255); d[k + 2] = clamp(d[k + 2] + v * 1.1, 0, 255);
    }
    ctx.putImageData(im, 0, 0);
    const r = rng(seed || 21); ctx.save(); ctx.lineCap = 'round';
    for (let i = 0; i < w * h / 9000; i++) { const x = r() * w, y = r() * h, a = r() * Math.PI, l = 3 + r() * 9; ctx.strokeStyle = r() < .5 ? 'rgba(120,100,80,.10)' : 'rgba(255,255,255,.35)'; ctx.lineWidth = .6 + r() * .6; ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + Math.cos(a) * l * .5 + r() * 2, y + Math.sin(a) * l * .5 + r() * 2, x + Math.cos(a) * l, y + Math.sin(a) * l); ctx.stroke(); }
    ctx.restore();
  }

  // ---------- crayon fill ----------
  function crayonFill(ctx, pts, color, o){
    o = o || {}; const b = bbox([pts], 6), c = mk(b.w, b.h), x = c.getContext('2d'), r = rng(o.seed || 1);
    if (o.base !== false) { ctx.save(); ctx.fillStyle = o.base || '#fbf8f1'; poly(ctx, pts, true); ctx.fill(); ctx.restore(); }
    x.translate(-b.x, -b.y); x.save(); poly(x, pts, true); x.clip();
    x.globalAlpha = o.alpha == null ? .93 : o.alpha; x.fillStyle = color; x.fillRect(b.x, b.y, b.w, b.h); x.globalAlpha = 1;
    const ang = o.angle == null ? -1.05 : o.angle, ca = Math.cos(ang), sa = Math.sin(ang), diag = Math.hypot(b.w, b.h), cx = b.x + b.w / 2, cy = b.y + b.h / 2;
    x.lineCap = 'round';
    const sp = (o.spacing || 2.6) * G;
    for (let i = -diag / 2; i < diag / 2; i += sp * (.7 + r() * .6)) {
      const px = cx - sa * i, py = cy + ca * i;
      x.strokeStyle = shade(color, (r() - .45) * (o.var == null ? .16 : o.var)); x.globalAlpha = (.16 + r() * .22) * (o.hatchK == null ? 1 : o.hatchK); x.lineWidth = (1 + r() * 2.4) * G;
      x.beginPath(); x.moveTo(px - ca * diag / 2, py - sa * diag / 2 + (r() - .5) * 3); x.quadraticCurveTo(px + (r() - .5) * 6, py + (r() - .5) * 6, px + ca * diag / 2, py + sa * diag / 2); x.stroke();
    }
    x.globalAlpha = 1;
    if (o.extra) o.extra(x);
    // pigment builds up along the edge
    x.globalAlpha = .42; x.strokeStyle = shade(color, -.14, .04); x.lineWidth = o.edge || 5; poly(x, pts, true); x.stroke();
    x.restore();
    erode(x, b, o.tooth == null ? .5 : o.tooth);
    ctx.drawImage(c, b.x, b.y);
  }
  // ---------- pencil / crayon line ----------
  function pencil(ctx, pts, closed, o){
    o = o || {}; const w = o.w || 3, b = bbox([pts], w * 3 + 4), c = mk(b.w, b.h), x = c.getContext('2d'), seed = o.seed || 3;
    x.translate(-b.x, -b.y); x.lineCap = 'round'; x.lineJoin = 'round'; x.strokeStyle = o.color || '#3b2f29';
    const P = closed ? pts.concat([pts[0]]) : pts;
    for (let i = 1; i < P.length; i++) {
      const p = P[i];
      x.globalAlpha = (o.alpha == null ? .9 : o.alpha) * (.78 + N.n2(p[0] * .08 / G + seed, p[1] * .08 / G) * .3);
      x.lineWidth = w * (.72 + N.n2(p[0] * .05 / G + 40 + seed, p[1] * .05 / G) * .6);
      x.beginPath(); x.moveTo(P[i - 1][0], P[i - 1][1]); x.lineTo(p[0], p[1]); x.stroke();
    }
    if (o.double !== false) { const q = wob(pts, closed, w * .4, .06, seed + 5); x.globalAlpha = .35; x.lineWidth = w * .5; poly(x, q.map(p => [p[0] + .5, p[1] + .4]), closed); x.stroke(); }
    erode(x, b, o.tooth == null ? .38 : o.tooth);
    ctx.drawImage(c, b.x, b.y);
  }
  function dot(ctx, x, y, r, color, hl){ ctx.save(); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); if (hl) { ctx.fillStyle = 'rgba(255,255,255,.9)'; ctx.beginPath(); ctx.arc(x - r * .32, y - r * .35, r * .3, 0, Math.PI * 2); ctx.fill(); } ctx.restore(); }
  function blush(ctx, x, y, rx, ry, col){ ctx.save(); ctx.translate(x, y); ctx.scale(1, ry / rx); const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rx); g.addColorStop(0, col || 'rgba(236,140,130,.55)'); g.addColorStop(1, 'rgba(236,140,130,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, rx, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }

  // ---------- torn paper cut-out edge ----------
  function cutout(ctx, b, masker, o){
    o = o || {}; const r = o.border || 10, pad = r + 14, bx = Math.floor(b.x - pad), by = Math.floor(b.y - pad), bw = Math.ceil(b.w + 2 * pad), bh = Math.ceil(b.h + 2 * pad);
    const m = mk(bw, bh), mx = m.getContext('2d'); mx.translate(-bx, -by); mx.fillStyle = '#000'; masker(mx);
    const dl = mk(bw, bh), dx = dl.getContext('2d');
    for (let k = 0; k < 28; k++) { const a = k / 28 * Math.PI * 2; dx.drawImage(m, Math.cos(a) * r, Math.sin(a) * r); dx.drawImage(m, Math.cos(a) * r * .55, Math.sin(a) * r * .55); }
    dx.drawImage(m, 0, 0);
    const bl = mk(bw, bh), bx2 = bl.getContext('2d'); bx2.filter = 'blur(' + (r * .35).toFixed(1) + 'px)'; bx2.drawImage(dl, 0, 0); bx2.filter = 'none';
    const im = bx2.getImageData(0, 0, bw, bh), d = im.data, nz = Noise(o.seed || 5);
    for (let j = 0; j < bh; j++) for (let i = 0; i < bw; i++) {
      const k = (j * bw + i) * 4, a = d[k + 3] / 255; if (a === 0) continue;
      const X = bx + i, Y = by + j, jag = (nz.n2(X / (2.4 * G), Y / (2.4 * G)) - .5) * .42 + (nz.n2(X / (11 * G), Y / (11 * G)) - .5) * .7;
      const v = a + jag > .5 ? 1 : 0; d[k] = 253; d[k + 1] = 251; d[k + 2] = 245; d[k + 3] = v * 255;
    }
    bx2.putImageData(im, 0, 0);
    ctx.save(); ctx.shadowColor = o.shadowColor || 'rgba(70,48,28,.3)'; ctx.shadowBlur = o.shadow == null ? 9 : o.shadow; ctx.shadowOffsetX = 2; ctx.shadowOffsetY = 4; ctx.drawImage(bl, bx, by); ctx.restore();
    // faint fibrous grey rim just inside the tear
    ctx.save(); ctx.globalAlpha = .18; ctx.globalCompositeOperation = 'multiply'; const rim = mk(bw, bh), rx = rim.getContext('2d'); rx.drawImage(bl, 0, 0); rx.globalCompositeOperation = 'destination-out'; rx.drawImage(bl, 1.2, 1.4); rx.globalCompositeOperation = 'source-in'; rx.fillStyle = '#8c7a66'; rx.fillRect(0, 0, bw, bh); ctx.drawImage(rim, bx, by); ctx.restore();
  }

  // ---------- figure: ordered parts drawn fill-then-line, back to front ----------
  function figure(ctx, parts, T, o){
    o = o || {}; const S = T.s, seed0 = o.seed || 1;
    const geo = parts.map((p, i) => {
      const g = {};
      const conv = d => sample(d, p.step || .6).map(sp => ({ pts: wob(xf(T.warp ? sp.pts.map(T.warp) : sp.pts, T), sp.closed, (p.wob == null ? .32 : p.wob) * S, .018, seed0 + i), closed: sp.closed }));
      if (p.fill) g.fill = conv(p.d);
      if (p.line) g.line = conv(p.line);
      return g;
    });
    if (o.cut !== false) {
      const sil = []; parts.forEach((p, i) => { if (p.fill && !p.inner) geo[i].fill.forEach(sp => sil.push(sp.pts)); });
      if (sil.length) cutout(ctx, bbox(sil, 0), mx => sil.forEach(pts => { poly(mx, pts, true); mx.fill(); }), { border: o.border || S * 2.4, seed: seed0 + 70, shadow: o.shadow, shadowColor: o.shadowColor });
    }
    parts.forEach((p, i) => {
      const lw = (p.lw || 1.9) * (o.lineS || S) * (o.lineScale || .44);
      if (p.fill) geo[i].fill.forEach(sp => {
        crayonFill(ctx, sp.pts, p.fill, { angle: p.hatch, hatchK: p.hatchK, var: p.var, base: p.base, seed: seed0 * 31 + i, extra: p.extra ? x => { x.save(); x.translate(T.x, T.y); x.rotate(T.r || 0); x.scale(S, S); p.extra(x); x.restore(); } : null, tooth: p.tooth, edge: Math.max(3, S * 1.1) });
        if (p.outline !== false) pencil(ctx, sp.pts, sp.closed, { w: lw, seed: seed0 + i, color: p.ink });
      });
      if (p.line) geo[i].line.forEach(sp => pencil(ctx, sp.pts, sp.closed, { w: lw, color: p.color, seed: seed0 + i, double: p.double }));
      if (p.dot) { const q = xf([T.warp ? T.warp([p.dot[0], p.dot[1]]) : [p.dot[0], p.dot[1]]], T)[0]; dot(ctx, q[0], q[1], Math.max(p.dot[2] * S, o.minDot || 0), p.color || '#2e2521', p.hl !== false); }
      if (p.blush) { const q = xf([T.warp ? T.warp([p.blush[0], p.blush[1]]) : [p.blush[0], p.blush[1]]], T)[0]; blush(ctx, q[0], q[1], p.blush[2] * S, p.blush[3] * S, p.color); }
      if (p.text) { const q = xf([[p.text[0], p.text[1]]], T)[0]; ctx.save(); ctx.fillStyle = p.color || '#3b2f29'; ctx.font = (p.size * S) + 'px "Long Cang", serif'; ctx.textAlign = 'center'; ctx.fillText(p.text[2], q[0], q[1]); ctx.restore(); }
    });
  }
  function silhouette(parts, T, o){
    o = o || {}; const S = T.s, seed0 = o.seed || 1, sil = [];
    parts.forEach((p, i) => { if (p.fill && !p.inner) sample(p.d, p.step || .6).forEach(sp => sil.push(wob(xf(T.warp ? sp.pts.map(T.warp) : sp.pts, T), sp.closed, (p.wob == null ? .32 : p.wob) * S, .018, seed0 + i))); });
    return sil;
  }
  function cutoutMany(ctx, sils, o){ const all = [].concat.apply([], sils); cutout(ctx, bbox(all, 0), mx => all.forEach(pts => { poly(mx, pts, true); mx.fill(); }), o); }
  function mirrorD(d){ let idx = 0; return d.replace(/[MLCQZ]|-?\d*\.?\d+(?:e[-+]?\d+)?/gi, t => { if (/^[MLCQZ]$/i.test(t)) { idx = 0; return t; } const out = idx % 2 === 0 ? String(-parseFloat(t)) : t; idx++; return out; }); }
  function mirrorParts(parts){ return parts.map(p => { const q = Object.assign({}, p); if (q.d) q.d = mirrorD(q.d); if (q.line) q.line = mirrorD(q.line); if (q.dot) q.dot = [-q.dot[0], q.dot[1], q.dot[2]]; if (q.blush) q.blush = [-q.blush[0], q.blush[1], q.blush[2], q.blush[3]]; if (q.hatch != null) q.hatch = Math.PI - q.hatch; return q; }); }
  return { setGrain, mirrorD, mirrorParts, silhouette, cutoutMany, rng, Noise, mk, shade, E, limb, sample, xf, wob, bbox, poly, initTooth, paper, crayonFill, pencil, dot, blush, cutout, figure };
})();
