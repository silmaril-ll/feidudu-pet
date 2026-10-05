// 肥嘟嘟要用到的画：身体（侧面 fatParts、正面 fatFront）、叶子、蛹、蝴蝶。
// 画法和随机种子都是固定的，每次画出来都一样。

const COL = { cat:'#8fc85a', catD:'#5a9538', catBelly:'#d3ea9e' };     // 肥嘟嘟侧面的绿、深绿、肚皮

const E = ART.E;

// 肥嘟嘟: a final-instar Papilio xuthus larva, side view facing left, sitting on y=0
function fatParts(o){
  o = o || {}; const P = [];
  [36, 48, 60, 72].forEach(x => P.push({ d: E(x, 1.2, 4.2, 3.4), fill: '#b5d98a', lw: 1.3 }));
  P.push({ d: E(118, .5, 5.5, 3.6), fill: '#b5d98a', lw: 1.3 });
  P.push({ d: 'M12,2 C4,2 2,-10 6,-20 C10,-42 30,-57 50,-53 C62,-51 70,-43 84,-41 C100,-39 118,-37 126,-25 C132,-15 130,-2 120,1 Z', fill: COL.cat, hatch: -1.25 });
  P.push({ d: 'M14,1 C40,-9 92,-11 127,-9 C129,-4 126,0 120,1 Z', fill: COL.catBelly, outline: false, inner: true, tooth: .35 });
  P.push({ line: 'M61,-46 C58,-32 58,-16 61,-1 M73,-42 C70,-30 70,-15 73,-1 M85,-40 C82,-28 82,-14 85,-1 M97,-38 C94,-27 94,-13 97,-1 M109,-35 C106,-25 106,-12 109,-1', lw: 1, color: COL.catD, double: false });
  P.push({ d: 'M49,-53 C44,-36 44,-16 48,-1 L57,-1 C53,-16 53,-34 58,-50 Z', fill: '#6f6a3b', outline: false, inner: true, tooth: .3 });
  [[51.5, -41], [50.5, -29], [51, -16]].forEach(p => P.push({ dot: [p[0], p[1], 1.5], color: '#a8dbef', hl: false }));
  P.push({ line: 'M100,-5 L114,-29 M86,-5 L97,-31', lw: 2.2, color: '#f4f2dd', double: false });
  // two big fake eyes on the hump (the whole reason it's cute)
  P.push({ d: E(40, -41, 6.6, 6), fill: '#2f2b26', lw: 1.2 });
  P.push({ d: E(40.5, -41, 4.4, 4), fill: '#e8efb2', outline: false });
  P.push({ dot: [40, -40.5, 2.1], color: '#2b2723' });
  P.push({ d: E(25, -33, 8.8, 8), fill: '#2f2b26', lw: 1.2 });
  P.push({ d: E(25.6, -33, 6, 5.5), fill: '#e8efb2', outline: false });
  P.push({ dot: [24.6, -32.5, 2.9], color: '#2b2723' });
  P.push({ blush: [15, -21, 5.5, 3.4] }); P.push({ blush: [46, -30, 4.5, 2.8] });
  P.push({ d: E(9.5, -8, 9.5, 9), fill: '#aebf70', hatch: -.4 });
  P.push({ line: 'M4.5,-5 Q7.5,-2.2 10.5,-5', lw: 1.3 });
  if (o.horns) P.push({ line: 'M8,-16 L6,-26 C1,-34 -6,-37 -14,-37 M6,-26 C6,-37 12,-44 20,-48', lw: 6, color: '#f08a2b', double: false });
  [16, 22, 28].forEach(x => P.push({ d: E(x, 1.8, 2, 2.2), fill: '#6b5a3a', outline: false }));
  return P;
}

// extra modules for 肥嘟嘟's book
const C2 = {
  leaf:'#4f8a3e', twig:'#8a6a4a', pupaG:'#a7c96f', pupaB:'#a98356', pupaD:'#4b4139',
  bfK:'#2e2925', bfY:'#f3e3a0', bfB:'#7fa9d9', bfO:'#ea8a3a'
};

function citrusLeaf(col, o){
  o = o || {};
  return [
    { line: 'M0,0 L-10,1.5', lw: 2.2, color: '#6b8f45', double: false },
    { d: 'M0,0 C12,-15 40,-19 70,-11 C83,-7.5 93,-3 101,0 C89,4 79,8 66,11.5 C40,17.5 12,15 0,0 Z', fill: col || C2.leaf, hatch: .25 },
    { line: 'M0,0 C30,-2 70,-2 101,0', lw: 1.1, color: o.rib || '#9ccb78', double: false },
    { line: 'M20,-1 C26,-6 32,-9 38,-11 M44,-1 C50,-6 56,-8 62,-9.5 M68,-1 C73,-4 78,-5 84,-5.5 M22,0 C28,5 34,8 40,10 M46,0 C52,5 58,7 64,8.5 M70,0 C75,3 80,4 86,4.5', lw: .8, color: o.vein || '#86b865', double: false }
  ];
}

function twig(pts, w, col){ return [{ d: ART.limb(pts, w), fill: col || C2.twig, hatch: -1.4, lw: 1.6 }]; }

function pupaParts(col, o){
  o = o || {}; const P = [];
  const body = 'M0,0 C-7,-8 -11,-24 -10,-36 C-9,-44 -14,-50 -12,-58 L-9,-68 L-5,-61 L-1,-69 L2,-60 C5,-52 11,-44 12,-34 C13,-20 8,-7 0,0 Z';
  P.push({ d: body, fill: col, hatch: -1.3 });
  if (o.dark) { P.push({ line: 'M-7,-38 C-2,-32 4,-26 9,-30 M-6,-44 C0,-40 6,-36 10,-38 M-4,-32 C0,-28 4,-24 7,-25', lw: 1.3, color: '#e9d78a', double: false }); P.push({ dot: [5, -30, 1.4], color: '#7fa9d9', hl: false }); }
  P.push({ line: 'M-10,-36 C-3,-28 6,-20 11,-28', lw: 1.1 });
  P.push({ line: 'M-8,-16 C-3,-13 3,-13 7,-15 M-6,-9 C-2,-7 2,-7 5,-9 M-12,-58 C-6,-52 2,-50 9,-46', lw: .9, color: o.dark ? '#2a241f' : '#6f7f45', double: false });
  if (o.shell) P.push({ line: 'M-9,-66 C-6,-58 -2,-58 1,-67', lw: 1.3, color: '#8c8468', double: false });
  return P;
}

function bfParts(o){
  o = o || {}; const P = [];
  const FW = 'M2,-10 C18,-24 40,-34 58,-36 C60,-28 56,-16 50,-6 C38,-2 20,0 3,-2 Z';
  const HW = 'M3,-1 C18,0 34,4 40,14 C42,22 36,30 28,32 L27,44 L23,33 C16,34 8,26 3,14 Z';
  const wob = o.crumpled ? 1.3 : .3;
  const side = (mir) => {
    const m = d => mir ? ART.mirrorD(d) : d, mx = v => mir ? -v : v, Q = [];
    Q.push({ d: m(HW), fill: C2.bfK, wob: wob, hatch: -.7 });
    Q.push({ d: m('M6,1 C16,2 28,6 32,14 C30,20 22,22 14,18 C8,14 6,8 6,1 Z'), fill: C2.bfY, outline: false, inner: true, wob: wob });
    Q.push({ line: m('M8,4 L26,16 M8,9 L22,20 M10,14 L18,22'), lw: .9, color: C2.bfK, double: false });
    Q.push({ dot: [mx(33), 23, 2.2], color: C2.bfB, hl: false }); Q.push({ dot: [mx(29), 28, 1.9], color: C2.bfB, hl: false });
    Q.push({ d: m(E(22, 28.5, 3.4, 2.9)), fill: C2.bfO, outline: false }); Q.push({ dot: [mx(22), 28.8, 1.3], color: C2.bfK, hl: false });
    Q.push({ d: m(FW), fill: C2.bfK, wob: wob, hatch: -.9 });
    Q.push({ d: m('M8,-8 C18,-14 28,-20 36,-24 L37,-21 C28,-16 18,-10 9,-5 Z M9,-4 C20,-8 30,-12 40,-15 L40,-12 C30,-9 20,-5 10,-2 Z'), fill: C2.bfY, outline: false, inner: true, wob: wob });
    [[42, -26], [46, -19], [47, -12], [44, -6.5]].forEach(p => Q.push({ d: m(E(p[0], p[1], 3.2, 2.2)), fill: C2.bfY, outline: false, inner: true }));
    [[54, -31], [55, -23], [53, -15]].forEach(p => Q.push({ dot: [mx(p[0]), p[1], 1.2], color: C2.bfY, hl: false }));
    return Q;
  };
  side(true).concat(side(false)).forEach(q => P.push(q));
  P.push({ d: E(0, 3, 2.8, 16), fill: C2.bfK });
  P.push({ line: 'M0,-10 L0,16', lw: .8, color: C2.bfY, double: false });
  P.push({ d: E(0, -15, 3.2), fill: C2.bfK });
  P.push({ line: 'M-1,-17 C-4,-25 -8,-31 -11,-35 M1,-17 C4,-25 8,-31 11,-35', lw: 1.1, double: false });
  P.push({ dot: [-11, -35, 1.4], color: C2.bfK, hl: false }); P.push({ dot: [11, -35, 1.4], color: C2.bfK, hl: false });
  return P;
}

// 肥嘟嘟 phone-grip tops: roundish silhouettes, print resolution
const GC = { body: '#8fc85a', bodyD: '#5a9538', belly: '#d3ea9e', band: '#6f6a3b', head: '#aebf70', ink: '#2f2b26', iris: '#e8efb2', dot: '#a8dbef' };

function eye(x, y, rx, ry){
  return [
    { d: E(x, y, rx, ry), fill: GC.ink, lw: 1.2 },
    { d: E(x + rx * .06, y, rx * .67, ry * .67), fill: GC.iris, outline: false },
    { dot: [x, y + ry * .05, rx * .33], color: '#2b2723' }
  ];
}

// B. head-on: a round green face; the two fake eyes do all the work
function fatFront(){
  const P = [];
  [-26, -9, 9, 26].forEach(x => P.push({ d: E(x, 1, 5, 3.4), fill: '#b5d98a', lw: 1.2 }));
  P.push({ d: 'M-52,-4 C-60,-42 -42,-98 0,-98 C42,-98 60,-42 52,-4 C36,4 -36,4 -52,-4 Z', fill: GC.body, hatch: -1.1 });
  P.push({ d: 'M-53,-6 C-36,-16 36,-16 53,-6 C50,-2 44,1 36,2 C12,5 -12,5 -36,2 C-44,1 -50,-2 -53,-6 Z', fill: GC.belly, outline: false, inner: true, tooth: .35 });
  P.push({ d: 'M-47,-70 C-34,-96 34,-96 47,-70 L42,-64 C30,-86 -30,-86 -42,-64 Z', fill: GC.band, outline: false, inner: true, tooth: .3 });
  [[-30, -80], [-11, -87], [11, -87], [30, -80]].forEach(p => P.push({ dot: [p[0], p[1], 1.7], color: GC.dot, hl: false }));
  P.push(...eye(-21, -52, 13.5, 12.8));
  P.push(...eye(21, -52, 13.5, 12.8));
  P.push({ blush: [-37, -30, 7, 4.2] }); P.push({ blush: [37, -30, 7, 4.2] });
  P.push({ d: E(0, -13, 10.5, 9.6), fill: GC.head, hatch: -.4 });
  P.push({ line: 'M-3.6,-10.8 Q0,-7.6 3.6,-10.8', lw: 1.2 });
  P.push({ dot: [-4, -15.5, 1.1], color: '#3b3226', hl: false }); P.push({ dot: [4, -15.5, 1.1], color: '#3b3226', hl: false });
  [-7, 0, 7].forEach(x => P.push({ d: E(x, -2, 1.8, 2), fill: '#6b5a3a', outline: false }));
  return P;
}
